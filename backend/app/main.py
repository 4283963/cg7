import asyncio
import random
import math
from datetime import datetime
from typing import Optional
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from pydantic import ValidationError

from .database import init_db
from .models import (
    SensorData, BatchSensorData, StressResult,
    AlertRecord, AlertRule, TopologyData, TenonNode, RealtimeUpdate,
    ErrorResponse
)
from .services import (
    NodeService, DataIngestionService, AlertService, NodeService
)
from .websocket_manager import ws_manager
from .castigliano import (
    CastiglianoCalculationError,
    InvalidMaterialPropertyError,
    InvalidGeometryError,
    NumericalInstabilityError,
)

logger = logging.getLogger(__name__)

_simulator_task = None
_simulator_running = False


async def data_simulator():
    """Background task that simulates sensor data for demo purposes."""
    global _simulator_running
    
    nodes = NodeService.get_all_nodes()
    base_displacements = {}
    t = 0
    
    for node in nodes:
        base_displacements[node.id] = random.uniform(20, 150)
    
    while _simulator_running:
        try:
            t += 1
            sensor_data_list = []
            
            for node in nodes:
                base = base_displacements[node.id]
                wave = 20 * math.sin(t / 15.0 + hash(node.id) % 10)
                drift = 5 * math.sin(t / 50.0)
                noise = random.gauss(0, 8)
                
                if node.id == "node-beam-center":
                    base += 80
                elif node.id == "node-tower-top":
                    base += 40
                
                if t % 100 == 0 and node.id == "node-beam-center":
                    base += 30
                
                displacement = base + wave + drift + noise
                displacement = max(5, displacement)
                
                sensor_data = SensorData(
                    node_id=node.id,
                    displacement_um=displacement,
                    timestamp=datetime.now()
                )
                sensor_data_list.append(sensor_data)
            
            results = DataIngestionService.ingest_batch(sensor_data_list)
            
            if ws_manager.connection_count > 0:
                updated_nodes = NodeService.get_all_nodes()
                alerts = AlertService.get_alerts(limit=5, acknowledged=False)
                
                update = RealtimeUpdate(
                    type="realtime_update",
                    nodes=updated_nodes,
                    alerts=alerts,
                )
                await ws_manager.broadcast(update.model_dump(mode="json"))
            
            await asyncio.sleep(2.0)
            
        except Exception as e:
            print(f"Simulator error: {e}")
            await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _simulator_task, _simulator_running
    
    init_db()
    print("Database initialized.")
    
    _simulator_running = True
    _simulator_task = asyncio.create_task(data_simulator())
    print("Data simulator started.")
    
    yield
    
    _simulator_running = False
    if _simulator_task:
        _simulator_task.cancel()
        try:
            await _simulator_task
        except asyncio.CancelledError:
            pass
    print("Data simulator stopped.")


app = FastAPI(
    title="古建骨架应力监测台 API",
    description="榫卯关节微米级沉降与受力安全预警系统 - 科学计算后端",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CastiglianoCalculationError)
async def castigliano_calculation_error_handler(
    request: Request, exc: CastiglianoCalculationError
) -> JSONResponse:
    error_type = type(exc).__name__
    detail = {
        "error": "castigliano_calculation_error",
        "error_type": error_type,
        "message": str(exc),
        "details": {
            "path": request.url.path,
            "method": request.method,
        }
    }
    logger.error(f"Castigliano error at {request.url.path}: {str(exc)}", exc_info=True)

    if isinstance(exc, NumericalInstabilityError):
        return JSONResponse(status_code=422, content=detail)
    elif isinstance(exc, (InvalidMaterialPropertyError, InvalidGeometryError)):
        return JSONResponse(status_code=400, content=detail)
    else:
        return JSONResponse(status_code=500, content=detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    detail = {
        "error": "request_validation_error",
        "error_type": "RequestValidationError",
        "message": "Input validation failed",
        "details": {
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    }
    logger.warning(f"Validation error at {request.url.path}: {exc.errors()}")
    return JSONResponse(status_code=422, content=detail)


@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    detail = {
        "error": "pydantic_validation_error",
        "error_type": "ValidationError",
        "message": "Data validation failed",
        "details": {
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    }
    logger.warning(f"Pydantic validation error at {request.url.path}: {exc.errors()}")
    return JSONResponse(status_code=422, content=detail)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    detail = {
        "error": "http_error",
        "error_type": f"HTTPException_{exc.status_code}",
        "message": str(exc.detail),
        "details": {
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        }
    }
    logger.debug(f"HTTP {exc.status_code} at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.exception_handler(ZeroDivisionError)
async def zero_division_error_handler(
    request: Request, exc: ZeroDivisionError
) -> JSONResponse:
    detail = {
        "error": "division_by_zero",
        "error_type": "ZeroDivisionError",
        "message": "A division by zero was prevented. This indicates invalid input parameters.",
        "details": {
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        }
    }
    logger.critical(
        f"ZERO DIVISION ERROR at {request.url.path}: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(status_code=500, content=detail)


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    detail = {
        "error": "internal_server_error",
        "error_type": type(exc).__name__,
        "message": "An unexpected internal error occurred. The issue has been logged.",
        "details": {
            "path": request.url.path,
            "method": request.method,
        }
    }
    logger.critical(
        f"UNHANDLED EXCEPTION at {request.url.path}: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(status_code=500, content=detail)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/topology", response_model=TopologyData)
async def get_topology():
    return NodeService.get_topology()


@app.get("/api/nodes", response_model=list[TenonNode])
async def get_all_nodes():
    return NodeService.get_all_nodes()


@app.get("/api/nodes/{node_id}", response_model=TenonNode)
async def get_node(node_id: str):
    node = NodeService.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.get("/api/nodes/{node_id}/history")
async def get_node_history(
    node_id: str,
    hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=500, ge=10, le=5000),
):
    from datetime import timedelta
    start_time = datetime.now() - timedelta(hours=hours)
    history = NodeService.get_node_history(node_id, start_time=start_time, limit=limit)
    return {"node_id": node_id, "data": history, "count": len(history)}


@app.post("/api/sensor/data", response_model=list[StressResult])
async def receive_sensor_data(batch: BatchSensorData):
    results = DataIngestionService.ingest_batch(batch.data)
    
    if ws_manager.connection_count > 0:
        updated_nodes = NodeService.get_all_nodes()
        update = RealtimeUpdate(
            type="realtime_update",
            nodes=updated_nodes,
            alerts=[],
        )
        await ws_manager.broadcast(update.model_dump(mode="json"))
    
    return results


@app.get("/api/alerts", response_model=list[AlertRecord])
async def get_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    level: Optional[str] = None,
    acknowledged: Optional[bool] = None,
):
    return AlertService.get_alerts(limit=limit, level=level, acknowledged=acknowledged)


@app.put("/api/alerts/{alert_id}/ack", response_model=AlertRecord)
async def acknowledge_alert(alert_id: str):
    alert = AlertService.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.get("/api/rules", response_model=list[AlertRule])
async def get_all_rules():
    return AlertService.get_all_rules()


@app.get("/api/rules/{node_id}", response_model=AlertRule)
async def get_rule(node_id: str):
    return AlertService.get_rule(node_id)


@app.put("/api/rules/{node_id}", response_model=AlertRule)
async def update_rule(node_id: str, rule: AlertRule):
    updated = AlertService.update_rule(node_id, rule)
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
    return updated


@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        nodes = NodeService.get_all_nodes()
        alerts = AlertService.get_alerts(limit=5, acknowledged=False)
        initial_update = RealtimeUpdate(
            type="initial_data",
            nodes=nodes,
            alerts=alerts,
        )
        await websocket.send_json(initial_update.model_dump(mode="json"))
        
        while True:
            data = await websocket.receive_text()
            pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
