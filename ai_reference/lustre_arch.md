# Lustre Architecture Layers

## Overview Diagram

```
+-----------------------------------------------------------------------------------+
|                                  APPLICATION                                       |
|                                                                                    |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                                      VFS                                           |
|                Linux Virtual File System Interface (kernel)                        |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                                CLIENT LAYERS                                       |
|                                                                                    |
|  +---------------------+  +---------------------+  +---------------------+         |
|  |      LLITE          |  |        LOV          |  |        LMV          |         |
|  | (Lustre Lite - VFS  |  | (Logical Object     |  | (Logical Metadata   |         |
|  |  Interface)         |  |  Volume)            |  |  Volume)            |         |
|  | lustre/llite/       |  | lustre/lov/         |  | lustre/lmv/         |         |
|  +---------------------+  +---------------------+  +---------------------+         |
|                |                    |                        |                     |
|                v                    v                        v                     |
|  +---------------------+  +---------------------+  +---------------------+         |
|  |        VVP          |  |       LOVSUB        |  |         MDC         |         |
|  | (VFS/VM/Posix)      |  | (LOV Sub-device)    |  | (MetaData Client)   |         |
|  | lustre/llite/       |  | lustre/lov/         |  | lustre/mdc/         |         |
|  +---------------------+  +---------------------+  +---------------------+         |
|                                    |                        |                      |
|                                    v                        |                      |
|  +---------------------+  +---------------------+           |                      |
|  |        PCC          |  |        OSC          |           |                      |
|  | (Persistent Client  |  | (Object Storage     |           |                      |
|  |  Cache)             |  |  Client)            |           |                      |
|  | lustre/llite/pcc.c  |  | lustre/osc/         |           |                      |
|  +---------------------+  +---------------------+           |                      |
|                                    |                        |                      |
+-----------------------------------------------------------------------------------+
                                    /|\
                                   / | \
                                  /  |  \
                                 /   |   \
                                /    |    \
                               /     |     \
+-----------------------------------------------------------------------------------+
|                                 NETWORKING                                         |
|                                                                                    |
|  +---------------------+  +---------------------+  +---------------------+         |
|  |       LNET          |  |      SOCKLND        |  |       Other         |         |
|  | (Lustre Networking) |  | (Socket LND)        |  |       LNDs          |         |
|  | lnet/lnet/          |  | lnet/klnds/socklnd/ |  | lnet/klnds/*/       |         |
|  +---------------------+  +---------------------+  +---------------------+         |
|                                                                                    |
+-----------------------------------------------------------------------------------+
                               /|\           /|\
                              / | \         / | \
                             /  |  \       /  |  \
                            /   |   \     /   |   \
                           /    |    \   /    |    \
                          /     |     \ /     |     \
+-----------------------------------------------------------------------------------+
|                                SERVER LAYERS                                       |
|                                                                                    |
|  +---------------------+  +---------------------+  +---------------------+         |
|  |        MGS          |  |        MDT          |  |        OST          |         |
|  | (Management Server) |  | (MetaData Target)   |  | (Object Storage     |         |
|  | lustre/mgs/         |  | lustre/mdt/         |  |  Target)            |         |
|  |                     |  |                     |  | lustre/ost/          |         |
|  +---------------------+  +---------------------+  +---------------------+         |
|           ^                      |       |                   |                     |
|           |                      |       |                   |                     |
|           |                      v       |                   v                     |
|           |             +---------------------+    +---------------------+         |
|           |             |        MDD          |    |        OFD          |         |
|           |             | (MetaData Device)   |    | (Object Filter      |         |
|           |             | lustre/mdd/         |    |  Device)            |         |
|           |             |                     |    | lustre/ofd/          |        |
|           |             +---------------------+    +---------------------+         |
|           |                      |                           |                     |
|           |                      v                           v                     |
|           |             +---------------------+    +---------------------+         |
|           |             |        OSD          |    |        OSD          |         |
|           |             | (Object Storage     |    | (Object Storage     |         |
|           |             |  Device)            |    |  Device)            |         |
|           |             | lustre/osd-*/       |    | lustre/osd-*/       |         |
|           |             +---------------------+    +---------------------+         |
|           |                                                                        |
|           |                                                                        |
|           |                      Communication Paths                               |
|           |                      ------------------                                |
|           |                                                                        |
|           |    ←----- Client → MGS: Configuration and setup                        |
|           |                                                                        |
|           ↓    ←----- Client → MDT: Metadata operations (open, stat, mkdir)        |
|                                                                                    |
|           ↑    ←----- Client → OST: Data operations (read, write)                  |
|           |                                                                        |
|           |    ←----- MDT → OST: File creation, size queries, quota                |
|           |                                                                        |
|           |    ←----- MDT ↔ MDT: Directory striping (DNE)                          |
|           |                                                                        |
|           └----- OST ↔ OST: File mirroring                                         |
|                                                                                    |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                               BACKEND STORAGE                                      |
|                                                                                    |
|  +---------------------+  +---------------------+  +---------------------+         |
|  |        LDISKFS      |  |        ZFS          |  |      Other FS       |         |
|  | (Lustre DISKFS)     |  | (ZFS Backend)       |  |      Backends       |         |
|  | lustre/ldiskfs/     |  | lustre/osd-zfs/     |  |                     |         |
|  +---------------------+  +---------------------+  +---------------------+         |
|                                                                                    |
+-----------------------------------------------------------------------------------+
```

## Detailed Layer Descriptions

### Application Layer
- **Description**: User applications that access the Lustre filesystem
- **Source**: N/A (external to Lustre)

### VFS Layer
- **Description**: Linux Virtual File System interface that provides the standard POSIX file system interface
- **Source**: Linux kernel (external to Lustre)

### Client Layers

#### LLITE (Lustre Lite)
- **Description**: Client-side VFS interface that translates VFS operations to Lustre operations
- **Source Directory**: `lustre/llite/`
- **Key Files**:
  - `file.c` - File operations
  - `dir.c` - Directory operations
  - `super25.c` - Superblock operations
  - `llite_lib.c` - Core functionality
  - `llite_internal.h` - Internal structures

#### LOV (Logical Object Volume)
- **Description**: Manages file striping across multiple OSTs
- **Source Directory**: `lustre/lov/`
- **Key Files**:
  - `lov_ea.c` - Extended attribute handling
  - `lov_object.c` - Object operations

#### LOVSUB (LOV Sub-device)
- **Description**: Represents a single stripe of a file
- **Source Directory**: `lustre/lov/`
- **Key Files**:
  - `lovsub_object.c` - Sub-object operations

#### LMV (Logical Metadata Volume)
- **Description**: Manages directory striping across multiple MDTs
- **Source Directory**: `lustre/lmv/`

#### VVP (VFS/VM/Posix)
- **Description**: Interfaces between the Linux VFS/VM and Lustre client
- **Source Directory**: `lustre/llite/`
- **Key Files**:
  - `vvp_dev.c`
  - `vvp_io.c`
  - `vvp_object.c`

#### MDC (MetaData Client)
- **Description**: Client interface to MDT servers
- **Source Directory**: `lustre/mdc/`

#### OSC (Object Storage Client)
- **Description**: Client interface to OST servers
- **Source Directory**: `lustre/osc/`

#### PCC (Persistent Client Cache)
- **Description**: Provides local caching of Lustre files on client SSDs
- **Source Directory**: `lustre/llite/`
- **Key Files**:
  - `pcc.c` - PCC implementation
  - `pcc.h` - PCC definitions

### Networking Layer

#### LNET (Lustre Networking)
- **Description**: Network abstraction layer that provides communication between Lustre components
- **Source Directory**: `lnet/lnet/`
- **Key Files**:
  - `lib-move.c` - Data movement
  - `module.c` - Module initialization
  - `api-ni.c` - Network interface API

#### SOCKLND (Socket LND)
- **Description**: Socket-based LNet Network Driver
- **Source Directory**: `lnet/klnds/socklnd/`
- **Key Files**:
  - `socklnd.c` - Socket LND implementation

#### Other LNDs
- **Description**: Other network drivers (IB, etc.)
- **Source Directory**: `lnet/klnds/*/`

### Server Layers

#### MGS (Management Server)
- **Description**: Stores and provides configuration information for the entire Lustre filesystem
- **Source Directory**: `lustre/mgc/` (client), `lustre/mgs/` (server)

#### MDT (MetaData Target)
- **Description**: Manages filesystem namespace (filenames, directories, permissions)
- **Source Directory**: `lustre/mdt/`
- **Key Files**:
  - `mdt_handler.c` - Request handling
  - `mdt_lib.c` - Core functionality
  - `mdt_mds.c` - MDS service
  - `mdt_internal.h` - Internal structures

#### MDD (MetaData Device)
- **Description**: Interfaces between MDT and storage
- **Source Directory**: `lustre/mdd/`

#### OST (Object Storage Target)
- **Description**: Manages file data storage
- **Source Directory**: `lustre/ost/`
- **Key Files**:
  - `ost_handler.c` - Request handling

#### OFD (Object Filter Device)
- **Description**: Interfaces between OST and OSD
- **Source Directory**: `lustre/ofd/`

#### OSD (Object Storage Device)
- **Description**: Interfaces between OFD and backend filesystem
- **Source Directory**:
  - `lustre/osd-ldiskfs/` - For ldiskfs backend
  - `lustre/osd-zfs/` - For ZFS backend
- **Key Files**:
  - `osd_handler.c` - Request handling
  - `osd_object.c` - Object operations

### Backend Storage Layer

#### LDISKFS
- **Description**: Modified ext4 filesystem used as Lustre backend
- **Source Directory**: `lustre/ldiskfs/`

#### ZFS
- **Description**: ZFS filesystem used as Lustre backend
- **Source Directory**: `lustre/osd-zfs/`
- **Key Files**:
  - `osd_scrub.c` - Scrubbing operations
  - `osd_object.c` - Object operations

## Communication Paths and Data Flow

### Basic Client-Server Communication
1. Applications make POSIX file system calls
2. VFS routes these calls to the Lustre client (LLITE)
3. LLITE translates these into Lustre operations:
   - Metadata operations go through MDC to MDT
   - Data operations go through LOV, which distributes across OSCs to OSTs
4. LNET handles all network communication between clients and servers
5. Servers process requests and interact with backend storage
6. Results flow back through the same path to the application

### Inter-Server Communication

#### MDT-OST Communication
- **File Creation**: When creating a file with striping, MDT communicates with OSTs to create objects
- **File Size/Attribute Updates**: MDT queries OSTs for file sizes during stat operations
- **Quota Enforcement**: MDT communicates with OSTs to enforce quota limits
- **HSM Operations**: MDT coordinates with OSTs for data migration
- **Source Directory**: `lustre/mdt/mdt_coordinator.c` handles coordination between MDT and OSTs

#### MDT-MDT Communication (DNE)
- **Directory Operations**: For striped directories, MDTs communicate with each other
- **Cross-MDT Operations**: Rename/link operations across directory stripes require MDT-MDT communication
- **Source Directory**: `lustre/mdt/mdt_restripe.c` handles directory striping operations

#### OST-OST Communication
- **Mirroring**: OSTs may communicate for file mirroring operations
- **Source Directory**: `lustre/ost/ost_handler.c`

### LNET Communication Details

LNET provides the networking infrastructure for all Lustre communications:

1. **Message Types**:
   - **Request/Response**: Basic RPC mechanism
   - **Bulk Data Transfer**: For large data transfers
   - **Event Notification**: For asynchronous events

2. **Communication Flow**:
   - Source component prepares message
   - LNET routes message to destination based on NID (Network Identifier)
   - LNET selects appropriate LND (LNET Network Driver) based on network type
   - Message is transmitted over physical network
   - Receiving LNET delivers to target component
   - Source Directory: `lnet/lnet/lib-move.c` handles message routing

3. **Key LNET Components**:
   - **Router**: Routes messages between different networks
   - **LND**: Network-specific drivers (socklnd, o2iblnd, etc.)
   - **Portal**: Message destination endpoints
   - **Match Entries**: Rules for message handling
   - Source Directory: `lnet/lnet/router.c` handles routing logic

## Key Components and Their Relationships

- **Client-side**: LLITE → LOV/LMV → LOVSUB/MDC → OSC → LNET
- **Server-side**: LNET → MDT/OST → MDD/OFD → OSD → Backend Storage (LDISKFS/ZFS)
- **Inter-server**: MDT ↔ OST, MDT ↔ MDT, OST ↔ OST (all via LNET)
- **Management**: MGS provides configuration for all components

## Special Features

- **PCC (Persistent Client Cache)**: Provides local caching on client SSDs
  - **Source Directory**: `lustre/llite/pcc.c`
  - **Communication**: Client-local, no network traffic for cached files

- **DOM (Data on MDT)**: Allows small files to be stored directly on MDT
  - **Source Directory**: `lustre/mdt/mdt_io.c`
  - **Communication**: Client → MDT for both metadata and data operations
  - **Function**: `mdt_dom_object_size()` - Handles DOM object size operations

- **DNE (Distributed Namespace)**: Allows directories to be striped across multiple MDTs
  - **Source Directory**: `lustre/mdt/mdt_restripe.c`
  - **Communication**: Client → MDT, MDT → MDT for cross-directory operations

- **HSM (Hierarchical Storage Management)**: Provides tiered storage capabilities
  - **Source Directory**: `lustre/mdt/mdt_hsm.c`, `lustre/mdt/mdt_coordinator.c`
  - **Communication**: MDT → OST → External Storage System

- **Nodemap Security**: Provides client identity mapping for multi-tenant security
  - **Source Directory**: `lustre/ptlrpc/nodemap_handler.c`
  - **Function**: `mdt_check_resource_ids()` - Validates client access permissions
  - **Communication**: Applied at server entry points (MDT/OST)
