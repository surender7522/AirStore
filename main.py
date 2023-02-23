import reedsolo
import orjson
import msgpack
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, Response
from controller.put_controller import ingest_file
from controller.get_controller import construct_file
from controller.list_controller import update_list, list_bucket_info
from typing import Union

app = FastAPI()


@app.get("/")
async def root():
    import time
    start = time.time()
    print("hello")
    end = time.time()
    print(end - start)
    return {"message": "Hello World","time": end-start}

@app.get("/list/{bucket}")
async def list_bucket(bucket: str):
    import time
    start = time.time()
    info = await list_bucket_info(bucket=bucket)
    end = time.time()
    return {"message": "success", "data": info, "time_taken": end-start}

@app.get("/get/{bucket}/{name}")
async def get_item(bucket: str, name: str, version: Union[int, None] = None):
    try:
        import time
        start = time.time()
        contents, content_type, size = await construct_file(bucket=bucket, name=name, version=version)
    except Exception as e:
        return {"error": str(e)}
    end = time.time()
    headers = {'Content-Disposition': 'attachment; filename={}'.format(name), "time_taken": str(end-start), "speed": "{} Mbps".format((size/1_000_000)/(end-start))}
    return Response(contents, headers=headers, media_type=content_type)

@app.post("/put/{bucket}/{name}")
async def create_upload_file(bucket: str, name: str, file: UploadFile):
    import time
    start = time.time()
    contents = await file.read()
    version = await ingest_file(content=contents, bucket=bucket, name=name, content_type=file.content_type,
                      size=file.size)
    # bg=BackgroundTasks()
    # bg.add_task(update_list, bucket, name,version, file.size, file.content_type)
    await update_list(bucket=bucket, filename=name, version=version, size=file.size, content_type=file.content_type)
    end = time.time()
    print(end - start)
    return {"message": "success", "time_taken": end-start, "speed": "{} Mbps".format((file.size/1_000_000)/(end-start))}
