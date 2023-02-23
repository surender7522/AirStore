from .put_controller import PARITY, DATA, WORDSIZE, NUMNODES, \
                            METACOPIES, NODEPATH, MATRIXTYPE
from .put_controller import _suggest_metadata_nodes, _save_metadata
import msgpack
import os

LISTFILENAME='list.internal'

async def _find_list_nodes(bucket: str):
    list_node_names = await _suggest_metadata_nodes(bucket=bucket, name=bucket+'_'+LISTFILENAME)
    existing_list_node = None
    for _node in list_node_names:
        try:
            t = open('{}/{}/{}'.format(NODEPATH, _node, bucket+'_'+LISTFILENAME), "r")
            t.close()
            existing_list_node = _node
        except FileNotFoundError:
            #print('{} node does not have metadata'.format(_node))
            pass
    return existing_list_node

async def list_bucket_info(bucket: str):
    existing_list_node = await _find_list_nodes(bucket=bucket)
    if not existing_list_node:
        return {"error": "No listing replica available"}
    with open('{}/{}/{}'.format(NODEPATH, existing_list_node, bucket+'_'+LISTFILENAME), "rb") as reader:
            content = reader.read()
            _unpacked_data = msgpack.unpackb(content)
            return _unpacked_data

async def update_list(bucket: str, filename: str, version: str, size: str, content_type: str):
    existing_list_node = await _find_list_nodes(bucket=bucket)
    list_node_names = await _suggest_metadata_nodes(bucket=bucket, name=bucket+'_'+LISTFILENAME)
    if existing_list_node:
        #read and recreate
        with open('{}/{}/{}'.format(NODEPATH, existing_list_node, bucket+'_'+LISTFILENAME), "rb") as reader:
            content = reader.read()
            _unpacked_data = msgpack.unpackb(content)
            _unpacked_data.append({
            "filename": filename,
            "version": version,
            "size": size,
            "content_type": content_type
            })
        for i in range(0, len(list_node_names)):
            try:
                os.remove('{}/{}/{}'.format(NODEPATH, list_node_names[i], bucket+'_'+LISTFILENAME))
            except FileNotFoundError:
                pass
    else:
        #create fresh list
        _unpacked_data = [{
            "filename": filename,
            "version": version,
            "size": size,
            "content_type": content_type
            }]
    
    await _save_metadata(existing_node=existing_list_node, data=msgpack.packb(_unpacked_data), 
                    node_names=list_node_names,file_name=bucket+'_'+LISTFILENAME) 