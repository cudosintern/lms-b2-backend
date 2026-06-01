from fastapi.responses import JSONResponse

def returnException(msg:str):
    return JSONResponse(
        status_code=404,
        content={"status":False,"message":msg,"data":None}
    )

def returnSuccess(data:any, message:str = "Completed"):
    return {"status":True,"message":message,"data":data}
