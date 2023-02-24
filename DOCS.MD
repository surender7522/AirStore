# Documentation

## Problems focused on:
### Erasure Coding
Used _pyjerasure_ library based on ```libjerasure2``` to enable data parity for split data chunks. Particularly this solution uses 'cauchy' variant of the algorithm for encode and decode.

The algorithm & splitting strategy is configured with the following variables:
* DATA
  * Specifies how many chunks object data will be broken into.
* PARITY
  * Specifies number of parity chunks to generate. System can handle these many corruptions or complete node failures.
* NUMNODES
  * Number of folders/nodes under ```test_env``` to simulate and test storage and failures(corrupting or deleting data in folders)
* METACOPIES
  * Number of nodes the metadata is copied to, for high resiliency and faster read, for now also hosts same number of listing metadata files.
* NODEPATH
  * Internal variable specifying ```test_env``` location
* MATRIXTYPE
  * Algorithm used for data parity encode, decoding and recovery, currently uses cauchy.
### Replicated metadata layer
Metadata is stored in a odd number replicated fashion, it contains info on chunk placement across nodes, versions, sizes and content types
### Minimal Deployed/Managed entities
Using disk replicated metadata info and clever hashing strategy, a lot of lookups and database layer is eliminated

There is only one element, the backend which can be deployed as a stateless container supported by hypercorn for multiple workers
### Fast RW for metadata and listing
For faster access to disk stored metadata, we use ```messagepack``` binary data format, it provides small filesize and faster orm than someother methods like protobuf, json, ion etc.

### Basic support for S3 api
Current implementation is a Proof-of-Concept of the architecture to support a object store and implements basic GET PUT functionality for objects, LIST for buckets as the author feels these features adds appropriate complexity for the PoC to prove its weight.

The current solution is not s3 compliant.

## Structure of the solution:
### Data RW:
* READ
  * To minimize lookup for chunks, we use a consistent hashing strategy based on the bucket name and filename utilizing them as seeds to generate node numbers which will have the metadata replicas for data
  * Once this is known, we query any available metadata which contains the mapping of chunk to its node and filenames
  * Once the available chunks are fetched, they are combined using libjerasure2, raises Exception if not enough data for recovery
  * NOTE: metadata step can be skipped in the future, using same strategy of hash creation of data chunks directly, but it needs more thought
* WRITE/PUT
  * Similar to above, the bucket, filename is used to select metadata nodes
  * Data is broken down with required parity info using libjerasure2 and chunk nodes are selected using hashes
  * Metadata is completed and packed into messagepack format on disk
* LIST
  * List follows similar strategy to metadata creation and is plugged into PUT api to update whenever new data is flowing through
  * Runs as a background task, so doesnt slow down PUT, can be more optimized dataformat wise and execution wise in the future


## Major features:
* Erasure coding
* Minimal deployment footprint to manage
* Stateless and horizontally scalable
* Easy recovery from major node crashes
* Configurable parity and algorithm

## Preliminary Performance:
* All apis have response times integrated in response.
* 1GB file uploads take 10 sec e2e (4+3 parity)
* Tentative testing can take place using HEY
## Load Test - TBD

## Suggested improvements:
* Clever datamodels needed for faster reads and updates
* Explore other data serialization format which allows segmented data updates or deletions without reading the whole metadata 
* Explore more optimized file access libraries/posix systems to reduce time to fetch objects 
* Build autonomous systems to create more copies taking into account number of surviving replicas, demand usage etc
