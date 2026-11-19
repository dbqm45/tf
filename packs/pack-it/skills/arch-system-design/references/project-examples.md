# Project examples — model solutions and the decisions that follow from them

Summaries of eight exercises from system-design-primer, rewritten as reusable patterns. Do not copy them whole.
Take from them the **shape of the problem** and **the decision that solves it**, and compute the numbers for your case
(the procedure in SKILL.md). Every example applies the same procedure: use cases and scope → estimates → high-level
design → deep dive → iterative scaling.

## Conversion factors for estimates
- A month has about 2.5 million seconds. 1 request/s is ~2.5 million requests a month. 40 requests/s is ~100 million a month,
  and 400 requests/s is ~1 billion a month.
- Powers of two (sizes and ranges):

  | Power | Value | Approximation | Bytes |
  |---|---|---|---|
  | 2⁸ | 256 | | |
  | 2¹⁰ | 1024 | a thousand | 1 KB |
  | 2¹⁶ | 65,536 | | 64 KB |
  | 2²⁰ | 1,048,576 | a million | 1 MB |
  | 2³⁰ | ~1.07·10⁹ | a billion | 1 GB |
  | 2³² | ~4.29·10⁹ | 4 billion (the unsigned `INT` range; signed ~2.1 billion) | 4 GB |
  | 2⁴⁰ | ~1.1·10¹² | a trillion | 1 TB |

- Identifier length: k characters from an alphabet of m symbols give mᵏ values. Base62 (`[a-zA-Z0-9]`, without characters
  requiring URL encoding) with 7 characters gives 62⁷ ≈ 3.5·10¹² values.

## The scaling ladder (from one server to millions of users)
Every rung is justified by a **measurement**: a load test, a profile, a bottleneck. Without a measurement you do not step onto the next one.
Often one or two steps from a given rung are enough.
1. **One server**: the application and the database on one machine, vertical scaling, basic metrics (CPU, memory, I/O,
   network). A static IP address and DNS. Only the needed ports open.
2. **Separation**: static files and user files to an object store, the database on a separate, managed
   machine (backups, multiple zones, encryption). A private network for everything except the entry point.
3. **Horizontal scaling**: a load balancer, several stateless servers in different zones, the database in primary +
   standby mode. A separate web server (reverse proxy) layer and application layer, and if needed separate servers for the read
   and write APIs. A CDN for static content.
4. **Read-heavy**: an in-memory cache (popular data, sessions) and read replicas. The application sends writes to
   the primary database and reads to the replicas.
5. **Variable traffic**: autoscaling with a minimum and maximum, infrastructure automation, metrics at the
   host and load balancer level, log analysis, external monitoring, on-call, error reporting
   (ops-observability).
6. **Large data and writes**: old data to a warehouse or an object store, federation, sharding, denormalization, part
   of the data in NoSQL, non-urgent work asynchronously through queues (be-database, be-messaging-outbox).

## Patterns from the exercises
| Exercise | Shape of the problem | Key decisions |
|---|---|---|
| **Pastebin / URL shortener** | few writes, 10× more reads, a short identifier, expiry | metadata in the database (key = identifier), content in an object store; the identifier as base62 from random data or a hash (e.g. MD5) with collision detection on write; popular entries in the cache; expired entries removed by a periodic job; statistics from logs in batches, because they need not be current |
| **Timeline and search (Twitter)** | a huge timeline read, a write fanned out to followers | **fan-out on write**: a post goes into the followers' ready timelines in the cache, so a read is one fetch of a list of identifiers + a multiget of many keys. For accounts with millions of followers **fan-out on read**: their posts are merged at read time (a hybrid model). The cache holds only a few hundred recent posts and only active users, and an inactive user's timeline is rebuilt from the database. Search: an inverted index with the query scattered to all shards and the results merged (scatter-gather) |
| **Web crawler** | a billion pages, cycles in the link graph, freshness | a link queue with a priority (a sorted set); processed pages with a **content signature**, and a similar signature lowers the priority instead of looping; duplicate addresses removed in batches, and duplicate content through a similarity measure (Jaccard, cosine); refreshing by the page's change frequency; **respect for `robots.txt`** and a per-domain request limit; its own DNS cache and connection pool; the inverted index and page descriptions as separate services fed from queues |
| **Personal budget (Mint)** | **write-heavy** (transactions daily, few visits), bank integrations | fetching transactions through a queue (a slow, unreliable source); raw data in an object store, and monthly aggregates in a separate table or warehouse; categorization from a merchant → category dictionary (small, in memory) with user corrections; a default budget from a template, and in the database only the user's overrides; notifications asynchronously; automatic updates only for active accounts |
| **Social graph** | the shortest path between people, the graph does not fit on one machine | BFS (an unweighted graph) on data split across servers with a lookup service; limiting hops between machines: batching friend queries for the same server, a split by region; **bidirectional BFS** (from the source and from the target); a limit on time or the number of steps; caching results and batch precomputation; a graph database when allowed |
| **Query result cache** | limited memory, popular queries, fast hits | **LRU**: a map + a doubly linked list, all operations O(1); a TTL in case the source changes; scaling by **splitting the cache across machines** with the machine chosen by the key's hash and **consistent hashing**. Rejected variants: a separate cache on every machine (a low hit rate), a full copy on every one (wastes memory) |
| **Sales rank by category** | 100× more reads than writes, the result refreshed every hour | **batch precomputation** from logs (MapReduce or a warehouse query): the sum of quantities by (category, product), then sorting; the result stored in a ready table and the cache, so a read computes nothing; old data to the warehouse |
| **Scaling to millions of users** | growing traffic without rewriting everything | the scaling ladder above |

## Cross-cutting patterns
- **Compute before you choose**: 4 writes/s are handled by one database, 2000 writes/s no longer (Mint), and 60,000 deliveries/s
  require an in-memory store (Twitter).
- **Separate the read path from the write path**: separate APIs, separate models (ready timelines, ready rankings,
  aggregates) and separate scaling (ddd-tactical-design: CQRS).
- **Precompute what can be precomputed**: batch results, fan-out on write, materialized views.
  The cost is staleness and space, so record how much staleness the business accepts.
- **Slow and unreliable dependencies** (banks, the network, notifications) you handle through a queue with retries
  and idempotency.
- **Uneven traffic** (hot keys, celebrities, popular queries) is the rule, not the exception. A cache helps,
  a special path for hot keys and a size limit (e.g. only the N most recent posts).
- **Keep only active data in the fast store**: the last month or active users. The rest you rebuild
  on demand or move to the warehouse.
- **Consistent hashing** when splitting a cache and data: after adding or removing a node only part of the keys move
  (~1/n), not almost all of them, as with `hash(key) mod n`. Virtual nodes even out the distribution.

## Object-oriented design exercises (for learning modelling)
The primer also has small object-oriented tasks: a hash table, an LRU cache, a call centre, a deck of cards,
a parking lot, a chat. They are useful as an exercise in class responsibilities and states (eng-design-principles). In a real project the model follows from the domain (ddd-tactical-design), not from the exercise.

## Sources
- [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) — `solutions/system_design`
  (pastebin, twitter, web_crawler, mint, social_graph, query_cache, sales_rank, scaling_aws) and
  `solutions/object_oriented_design`; licence CC BY 4.0, © Donne Martin
- D. Karger et al., "Consistent hashing and random trees" (1997), i.e. consistent hashing

Described in our own words, with changes and additions.
