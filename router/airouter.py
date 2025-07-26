# # author : chris-jyp
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from datetime import datetime
from service.training import predict_and_recommend_service
from database.generatereceipt import FunctionAI
from database.generateitems import GenerateItems
from pydantic import BaseModel

router = APIRouter()

class PredictAndRecommendRequest(BaseModel):
    username: str

class InsertReceiptsRequest(BaseModel):
    username: str
    status: str = "recent"
    num: int = 5

class SimulateItemsRequest(BaseModel):
    username: str
    num_receipts: int = 10

@router.post("/predictandrecommend")
def predict_and_recommend(request: PredictAndRecommendRequest = Body(...)):
    result = predict_and_recommend_service(request.username)
    print("result:", result)
    if "error" in result:
        result['code'] = 200
        result['status'] = 'success'
        result['message'] = result['error']
        result.pop('error')
        return JSONResponse(status_code=200, content=result)
    safe = jsonable_encoder(
        result,
        custom_encoder={ObjectId: lambda oid: str(oid)}
    )
    return JSONResponse(status_code=200, content=safe)

@router.post("/receipts/insert")
def insert_receipts(request: InsertReceiptsRequest = Body(...)):
    try:
        ai = FunctionAI()
        ai.insert_receipt_to_db(username=request.username, status=request.status, num=request.num)
        return {
            "message": "Receipts inserted successfully",
            "username": request.username,
            "status": request.status,
            "num": request.num
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/items/simulate")
def simulate_items(request: SimulateItemsRequest = Body(...)):
    try:
        generator = GenerateItems()
        simulated_receipts = generator.process_receipts_to_items(username=request.username, num_receipts=request.num_receipts)
        content = jsonable_encoder({
            "message": "Simulated items processed successfully",
            "username": request.username,
            "num_receipts": request.num_receipts,
            "data": simulated_receipts,
        }, custom_encoder={
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid)
        })
        return JSONResponse(status_code=200, content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))