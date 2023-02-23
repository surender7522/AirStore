import pyjerasure
from random import Random, randint
from uuid import uuid4
import msgpack
import os

# Magic Numbers we assumed
PARITY = 3
DATA = 5
WORDSIZE = 8
NUMNODES = 9
METACOPIES = 3 # Number of metadata copies to make (on distinct nodes)
NODEPATH = './test_env' # To simulate multiple nodes
MATRIXTYPE = 'cauchy'

async def _create_metadata(existing_node, bucket, name, content_type, size, chunk_nodes, chunk_files, lengths):
    '''
    
    '''
    # Read and create metadata if already exists
    version=None
    chunks=[]
    for i in range(0, len(chunk_nodes)):
        if len(lengths) >=  i:
            lengths.append(0)
        chunks.append({
            "node": chunk_nodes[i],
            "name": chunk_files[i],
            "length": lengths[i]
        })
    if existing_node:
        with open('{}/{}/{}'.format(NODEPATH, existing_node, '{}_{}.meta'.format(bucket, name)), "rb") as reader:
            content = reader.read()
            _unpacked_data = msgpack.unpackb(content)
        _vers = _unpacked_data.get('versions')
        _vers[str(int(_unpacked_data.get('latest_version'))+1)] = {
            "content_type": content_type,
	        "size": size,
	        "chunks": chunks
        }
        _unpacked_data['versions'] = _vers
        _unpacked_data['latest_version']=str(int(_unpacked_data.get('latest_version'))+1)
        version=_unpacked_data['latest_version']
        return msgpack.packb(_unpacked_data), version
    else:
        _unpacked_data = {
            "filename": name,
            "bucket": bucket,
            "latest_version": "1",
            "versions": {
                "1": {
                    "content_type": content_type,
                    "size": size,
                    "chunks": chunks
                }
            }
        }
        return msgpack.packb(_unpacked_data), '1'

async def _suggest_chunk_nodes():
    '''
    Randomly select nodes from available ones, if repeat, do (n+1)%NUMNODES + 1
    '''
    s=set()
    while len(s) < DATA+PARITY:
        _random_int = randint(1, NUMNODES)
        while _random_int in s:
            _random_int = (_random_int+1)%NUMNODES + 1
        s.add(_random_int)
    node_names = [str(n) for n in s]
    file_names = []
    for _ in range(0, DATA+PARITY):
        file_names.append(str(uuid4()))
    return node_names, file_names
    

async def _suggest_metadata_nodes(bucket: str, name: str):
    '''
    We need to use simple hashing function to map our bucketname, name combo to 
    Node name.
    We will use this same hash function when getting the object as a first step
    to get metadata node
    '''
    dice = Random((bucket+name).__hash__())
    return [str(dice.randint(1, NUMNODES)) for _ in range(0, METACOPIES)]

async def _save_data(data: list, node_names:list, file_names: list):
    '''
    Save chunk data
    '''
    for i in range(0, len(node_names)):
        with open('{}/{}/{}'.format(NODEPATH, node_names[i], file_names[i]), "wb") as writer:
            writer.write(data[i])

async def _save_metadata(existing_node, data, node_names: list, file_name):
    '''
    Save metadata
    '''
    # Clear out old metadata if exists, then create new
    if existing_node:
        #delete files
        for i in range(0, len(node_names)):
            try:
                os.remove('{}/{}/{}'.format(NODEPATH, node_names[i], file_name))
            except FileNotFoundError:
                pass
    for i in range(0, len(node_names)):
        with open('{}/{}/{}'.format(NODEPATH, node_names[i], file_name), "wb") as writer:
            writer.write(data)

async def ingest_file(content: str, bucket: str, name: str, content_type: str, size: str):
    '''
    Ingests file into 4 data + 3 parity erasure format - 7 data blocks created
    '''
    
    # divide string into 4(DATA) parts
    parts = []
    lengths = []
    _size = len(content)
    for i in range(0,DATA-1):
        parts.append(content[i*(_size//DATA):(i+1)*(_size//DATA)])
        lengths.append(len(parts[-1]))
    parts.append(content[(DATA-1)*(_size//DATA) : ])
    lengths.append(len(parts[-1]))
    # create coded data
    matrix_type = MATRIXTYPE
    k = DATA  # Number of data blocks
    m = PARITY  # Number of coding blocks. This is also the maximum number of blocks that can be lost.
    w = WORDSIZE  # Word Size

    matrix = pyjerasure.Matrix(matrix_type, k, m, w)
    coded_data = pyjerasure.encode_from_blocks(matrix, parts)
    # print("CODED DATA {}".format(coded_data))

    # save it in 7(DATA+PARITY) of the folders on test_env simulating 9(NUMNODES) nodes
    node_names, file_names = await _suggest_chunk_nodes()
    print(node_names, file_names)
    await _save_data(data=coded_data, node_names=node_names, file_names=file_names)

# Check if existing metadata exists
    existing_meta_node_names = await _suggest_metadata_nodes(bucket=bucket, name=name)
    existing_metadata_node = None
    for _node in existing_meta_node_names:
        try:
            _ = open('{}/{}/{}'.format(NODEPATH, _node, '{}_{}.meta'.format(bucket, name)), "rb")
            existing_metadata_node = _node
        except FileNotFoundError:
            #print('{} node does not have metadata'.format(_node))
            pass
    # create metadata info
    metadata,version=await _create_metadata(existing_node=existing_metadata_node, bucket=bucket, 
                              name=name, content_type=content_type, size=size,
                              chunk_nodes=node_names, chunk_files=file_names, lengths=lengths)
    
    
    # save metadata on PARITY number of nodes with chunk node info, file metadata
    meta_node_names = await _suggest_metadata_nodes(bucket=bucket, name=name)
    await _save_metadata(existing_node=existing_metadata_node, data=metadata,
                           node_names=meta_node_names,
                          file_name='{}_{}.meta'.format(bucket, name))
    return version
