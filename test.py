import pyjerasure

data = [
  b"hello this is a long string purposely built to test how long a string this library can take",
  b"world",
  b"data-123",
  b"data-0123456789A",
]

matrix_type = "rs_r6"
k = 4  # Number of data blocks
m = 2  # Number of coding blocks. This is also the maximum number of blocks that can be lost.
w = 8  # Word Size

matrix = pyjerasure.Matrix(matrix_type, k, m, w)

coded_data = pyjerasure.encode_from_blocks(matrix, data)
print(coded_data)

missing = [1, 3]
for i in missing:
  coded_data[i] = b""
print(coded_data)

restored = pyjerasure.decode_from_blocks(matrix, coded_data, missing)
print("Restored {}".format(restored))
ss = restored[0].decode().strip('\x00')
print(ss.encode())
