from .put_controller import _suggest_metadata_nodes
from .put_controller import PARITY, DATA, WORDSIZE, NUMNODES, \
                            METACOPIES, NODEPATH, MATRIXTYPE
import msgpack
import pyjerasure

async def construct_file(bucket: str, name: str, version: int = None):
    '''
    Construct the file by decoding data from the 7 blocks (4+3 parity),
      we use special access to determine where our 7 blocks are located
    '''
    # Consistent hashing of bucket, name into 7 blocks to determine the nodes
    meta_node_names = await _suggest_metadata_nodes(bucket=bucket, name=name)
    existing_metadata_node = None
    for _node in meta_node_names:
        try:
            _ = open('{}/{}/{}'.format(NODEPATH, _node, '{}_{}.meta'.format(bucket, name)), "r")
            existing_metadata_node = _node
        except FileNotFoundError:
            #print('{} node does not have metadata'.format(_node))
            pass
    if not existing_metadata_node:
        raise Exception("No such item exists")
    # fetch metadata
    with open('{}/{}/{}'.format(NODEPATH, existing_metadata_node, '{}_{}.meta'.format(bucket, name)), "rb") as reader:
            content = reader.read()
            _unpacked_data = msgpack.unpackb(content)
            if version is None:
                _ver = _unpacked_data['versions'][_unpacked_data['latest_version']]
            elif int(_unpacked_data['latest_version'])>=version and version > 0:
                _ver = _unpacked_data['versions'][str(version)]
            else:
                raise Exception("Cannot find specified version {}, latest version is {}".format(
                    version, _unpacked_data['latest_version']
                ))
            chunks = _ver['chunks']
            content_type = _ver['content_type']
            size = _ver['size']
    print(_unpacked_data)
    # fetch all the available blocks
    data=[]
    missing=[]
    for i in range(0, len(chunks)):
        try:
            with open('{}/{}/{}'.format(NODEPATH, chunks[i]['node'], chunks[i]['name']), "rb") as reader:
                data.append(reader.read())
        except Exception:
            data.append(b'')
            missing.append(i)
    if not missing:
        data[1]=b''
        missing.append(1)
    # decode and respond
    matrix_type = MATRIXTYPE
    k = DATA  # Number of data blocks
    m = PARITY  # Number of coding blocks. This is also the maximum number of blocks that can be lost.
    w = WORDSIZE  # Word Size

    matrix = pyjerasure.Matrix(matrix_type, k, m, w)
    restored = pyjerasure.decode_from_blocks(matrix, data, missing,data_only=True)
    
    if not restored:
        raise Exception('Cannot recover data!')
    z=[]
    for it in range(0,len(restored)):
        z.append(restored[it][:chunks[it]['length']])
    finals=b''
    for x in z:
        finals+=x
    return finals, content_type, size
