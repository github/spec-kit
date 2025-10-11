Change Log
==========

This change log is maintained by `src.ts/_admin/update-changelog.ts` but may also be manually updated.

ethers/v6.15.0 (2025-07-01 11:24)
---------------------------------

  - Allow non-canonical S values in Signatures moving errors to access-time ([#5013](https://github.com/ethers-io/ethers.js/issues/5013); [9944ec9](https://github.com/ethers-io/ethers.js/commit/9944ec94b154b4f8fdfeefb81a1e47b28fd907bc)).

ethers/v6.14.4 (2025-06-12 23:16)
---------------------------------

  - Fixed serialization of EIP-7702 transactions with leading 0-bytes ([#4916](https://github.com/ethers-io/ethers.js/issues/4916); [389dc03](https://github.com/ethers-io/ethers.js/commit/389dc0381222206011037792fd575c36da25abbf)).

ethers/v6.14.3 (2025-05-26 18:55)
---------------------------------

  - Fixed non-normalized yParity on EIP-7702 JSON-RPC responses ([#4985](https://github.com/ethers-io/ethers.js/issues/4985); [a8803ca](https://github.com/ethers-io/ethers.js/commit/a8803ca4dce20d2dededed8da65e80f2a8770fb1)).

ethers/v6.14.2 (2025-05-26 18:03)
---------------------------------

  - Fixed call stack overflow in makeError stringify for recursive structures ([#4977](https://github.com/ethers-io/ethers.js/issues/4977), [#4978](https://github.com/ethers-io/ethers.js/issues/4978); [52a0522](https://github.com/ethers-io/ethers.js/commit/52a052210919a35b0b0b38e357b3003ac8259fce)).
  - Explicitly throw error on gunzip failure to prevent uncaught exception ([#4873](https://github.com/ethers-io/ethers.js/issues/4873), [#4874](https://github.com/ethers-io/ethers.js/issues/4874); [fe98f98](https://github.com/ethers-io/ethers.js/commit/fe98f985e38e7540108b20d7966cca3f85d620f3)).
  - Skip additional receipt fetch for single confirmation requests ([#4972](https://github.com/ethers-io/ethers.js/issues/4972); [243cb02](https://github.com/ethers-io/ethers.js/commit/243cb02c52e33c8e09b637ae775e520c1cd672d3)).
  - Update EtherscanProvider to use their v2 API ([#4975](https://github.com/ethers-io/ethers.js/issues/4975); [5e09aa1](https://github.com/ethers-io/ethers.js/commit/5e09aa1fe4e216a89875bab768bec484aeaf553d)).

ethers/v6.14.1 (2025-05-15 14:17)
---------------------------------

  - Fix JSON-RPC authorizationList signature entries encoded as DATA instead of QUANTITY values ([#4916](https://github.com/ethers-io/ethers.js/issues/4916); [135db72](https://github.com/ethers-io/ethers.js/commit/135db722756b81f44f55441e1e2d24ef4f85f216)).

ethers/v6.14.0 (2025-05-06 22:02)
---------------------------------

  - Remove BlockscoutProvider temporarily until custom error issues are fixed ([805a8b3](https://github.com/ethers-io/ethers.js/commit/805a8b3aba26998a1e25055e9d3dd41c01ebbba0)).
  - EIP-7702 support ([#4916](https://github.com/ethers-io/ethers.js/issues/4916); [db490e1](https://github.com/ethers-io/ethers.js/commit/db490e1afaaa139be9cb38e6b50a1bc4ef28e075), [e7c1bdf](https://github.com/ethers-io/ethers.js/commit/e7c1bdf6f0a5d6f976dddd6375e76445ac6851fc)).
  - Added support for to override fetch init options in the Browser ([#3895](https://github.com/ethers-io/ethers.js/issues/3895); [844ae68](https://github.com/ethers-io/ethers.js/commit/844ae68a96deabc4d5f053dad5f1112b06f08d9a)).
  - Added EIP-6963 discovery to BrowserProvider ([f5469dd](https://github.com/ethers-io/ethers.js/commit/f5469dd0e0719389d51e0106ee36d07a7ebef875)).
  - Accept modern KZG library API while exposing legacy API ([#4841](https://github.com/ethers-io/ethers.js/issues/4841); [e5036e7](https://github.com/ethers-io/ethers.js/commit/e5036e778624fea957dd847f7be1a9f148b8997e)).
  - Added CommunityResourcable to exports ([#4776](https://github.com/ethers-io/ethers.js/issues/4776); [bca8d1b](https://github.com/ethers-io/ethers.js/commit/bca8d1b549569e6f7793f07fcc46dfd731e37d2b)).

ethers/v6.13.7 (2025-04-25 21:50)
---------------------------------

  - Fix FallbackProvider coalescing call exceptions when backends return slightly different error message ([268a0ac](https://github.com/ethers-io/ethers.js/commit/268a0ac5af6a2a59c240195d75ed19047731c6c0)).
  - Fixed Infura BSC network URLs ([#4951](https://github.com/ethers-io/ethers.js/issues/4951); [d01b4cb](https://github.com/ethers-io/ethers.js/commit/d01b4cb84b2f00dd04dc5317600a52f1fcf9b316)).

ethers/v6.13.6 (2025-03-21 18:21)
---------------------------------

  - Implicitly use EIP-7702 if authorizationList is given and non-empty ([#4961](https://github.com/ethers-io/ethers.js/issues/4961); [e7c1bdf](https://github.com/ethers-io/ethers.js/commit/e7c1bdf6f0a5d6f976dddd6375e76445ac6851fc)).
  - Initial EIP-7702 support ([#4916](https://github.com/ethers-io/ethers.js/issues/4916); [db490e1](https://github.com/ethers-io/ethers.js/commit/db490e1afaaa139be9cb38e6b50a1bc4ef28e075)).
  - Added support for to override fetch init options in the Browser ([#3895](https://github.com/ethers-io/ethers.js/issues/3895); [844ae68](https://github.com/ethers-io/ethers.js/commit/844ae68a96deabc4d5f053dad5f1112b06f08d9a)).
  - Added EIP-6963 discovery to BrowserProvider ([f5469dd](https://github.com/ethers-io/ethers.js/commit/f5469dd0e0719389d51e0106ee36d07a7ebef875)).
  - Merge: e5036e77 158f5d02     Merge branch 'main' into wip-v6.14 ([e7165a6](https://github.com/ethers-io/ethers.js/commit/e7165a6151e1fddcc9b8f4f30dfc13ee0a7d6f87)).
  - tests: squelch the noisy runtime console API event in browser tests ([79428fd](https://github.com/ethers-io/ethers.js/commit/79428fd44950ca21e9cc1b6f850122461217b0b3)).
  - tests: added faucet key environment for browser CI tests ([27d42af](https://github.com/ethers-io/ethers.js/commit/27d42af134bec099164e7afd03420c3dad53e3a9)).
  - tests: better runtime exception output for browser tests ([0beed25](https://github.com/ethers-io/ethers.js/commit/0beed258242cff7029ef1806ad0ff4955cb135c1)).
  - tests: added more debug endpoints to browser tests ([33bbf66](https://github.com/ethers-io/ethers.js/commit/33bbf662213b5d4a00901e490fd432dbeeb1a26b)).
  - tests: added JSON-RPC tests to web browser CI ([1c0c23c](https://github.com/ethers-io/ethers.js/commit/1c0c23c084e389390ce00e5a421267a4f8bdef0d)).
  - tests: added browser tests for sending ([afd613a](https://github.com/ethers-io/ethers.js/commit/afd613a2a0c9fb548805ed36e23ad9a5d4bcc239)).
  - tests: debugging browser tests failing to launch ([d1baa74](https://github.com/ethers-io/ethers.js/commit/d1baa741f6b272ba692e0e78787cacb1bd42a8b4)).
  - tests: fix assert call for browser assert ([1806bbd](https://github.com/ethers-io/ethers.js/commit/1806bbde27523933fb140ad985426f94e0286faf)).
  - tests: inlcude more node tests in the browser tests ([92fd5d1](https://github.com/ethers-io/ethers.js/commit/92fd5d1f47c640caa7100bcccf0b133e866989e6)).
  - tests: move more tests to dev network ([996f30c](https://github.com/ethers-io/ethers.js/commit/996f30c674002cea316fa7aa3929f43409f934bc)).
  - tests: debugging CI browser failure ([ce7212d](https://github.com/ethers-io/ethers.js/commit/ce7212d03d6867081603794f0480f31d053823c4)).
  - tests: debugging CI browser failure ([f1821a6](https://github.com/ethers-io/ethers.js/commit/f1821a696763938ca9d44815bdcd5cc043eb3900)).
  - tests: debugging CI browser failure ([cc9119c](https://github.com/ethers-io/ethers.js/commit/cc9119cecb6b970544861642861807c520eb763b)).
  - tests: debugging CI browser failure ([3ac33f9](https://github.com/ethers-io/ethers.js/commit/3ac33f9a40e40dabf9c19b8cc7114ce9897a3646)).
  - tests: debugging CI browser failure ([25b11ee](https://github.com/ethers-io/ethers.js/commit/25b11ee0eaa57293fe981b9b6b19bdae7d4db169)).
  - tests: debug CI failing ([3bcbcae](https://github.com/ethers-io/ethers.js/commit/3bcbcaeb025c530717b15c5ba099d320fdd9f934)).
  - tests: added circular support to browser-safe inspect ([3854b39](https://github.com/ethers-io/ethers.js/commit/3854b39763a2a57f363bf9bf925adcc27002bde1)).
  - tests: added browser-safe inspect for tests ([e299a31](https://github.com/ethers-io/ethers.js/commit/e299a31ecb9017baf07c58bb927c2e718ebeb447)).
  - tests: fix for browser CI tests ([74a68bc](https://github.com/ethers-io/ethers.js/commit/74a68bcc4976e48a00f57f5279664551b47b6840)).
  - tests: adding debug info to local JsonPrcProvider ([c508538](https://github.com/ethers-io/ethers.js/commit/c5085385563c57c7958be1ab413079dc8409c8c4)).
  - tests: temporarily remove QuickNode ([499ed8c](https://github.com/ethers-io/ethers.js/commit/499ed8c4bb91b918148c348b805ce753584065b6)).
  - Accept modern KZG library API while exposing legacy API ([#4841](https://github.com/ethers-io/ethers.js/issues/4841); [e5036e7](https://github.com/ethers-io/ethers.js/commit/e5036e778624fea957dd847f7be1a9f148b8997e)).
  - Added CommunityResourcable to exports ([#4776](https://github.com/ethers-io/ethers.js/issues/4776); [bca8d1b](https://github.com/ethers-io/ethers.js/commit/bca8d1b549569e6f7793f07fcc46dfd731e37d2b)).

ethers/v6.13.5 (2025-01-04 15:26)
---------------------------------

  - Use local dev net for testing Typed API to prevent tests getting throttled ([7654ee3](https://github.com/ethers-io/ethers.js/commit/7654ee3c6487171a4e13207accfc90f93a22b0fc)).
  - Fixed bad logic for searching prefetched transactions by hash ([#4868](https://github.com/ethers-io/ethers.js/issues/4868); [ef3c9bc](https://github.com/ethers-io/ethers.js/commit/ef3c9bc3afb9e36a073bbd3572e9021a852bd2c4)).
  - Add newline delimiter to IPC providers for broader support ([#4847](https://github.com/ethers-io/ethers.js/issues/4847); [474a8de](https://github.com/ethers-io/ethers.js/commit/474a8ded2b94a563067d3b4dd5f60ec0725b9a27)).

ethers/v6.13.4 (2024-10-10 18:01)
---------------------------------

  - Updated dependencies ([1d717ef](https://github.com/ethers-io/ethers.js/commit/1d717ef940b77d4ca9b350aa3aa159a40a547ac0)).
  - Fixed bug in JSON-RPC error checking ([#4827](https://github.com/ethers-io/ethers.js/issues/4827), [#4837](https://github.com/ethers-io/ethers.js/issues/4837), [#4851](https://github.com/ethers-io/ethers.js/issues/4851); [be3e6b1](https://github.com/ethers-io/ethers.js/commit/be3e6b14433bc88ad8c0c98a4f3a2a627cea6b99)).

ethers/v6.13.3 (2024-09-30 22:08)
---------------------------------

  - Allow CCIP-read to continue during low-level fetch failures ([#4842](https://github.com/ethers-io/ethers.js/issues/4842); [1c31f95](https://github.com/ethers-io/ethers.js/commit/1c31f95f7a1e4993ca0f1706002a975a0060dd88)).

ethers/v6.13.2 (2024-07-25 17:54)
---------------------------------

  - Prevent mutating transactions when signing ([#4789](https://github.com/ethers-io/ethers.js/issues/4789); [1a51af8](https://github.com/ethers-io/ethers.js/commit/1a51af85397283601db77ca61d5596b145e7f2cb)).

ethers/v6.13.1 (2024-06-18 02:09)
---------------------------------

  - Update ws package to address possible DoS vulnerability ([a4b1d1f](https://github.com/ethers-io/ethers.js/commit/a4b1d1f43fca14f2e826e3c60e0d45f5b6ef3ec4)).

ethers/v6.13.0 (2024-06-04 01:01)
---------------------------------

  - Added Options for BrowserProvider ([#4707](https://github.com/ethers-io/ethers.js/issues/4707); [33bb0bf](https://github.com/ethers-io/ethers.js/commit/33bb0bf30e1e6a699c24415a1edf0fa4ed28b6aa)).
  - Fix Result deep toObject when a parent is an Array ([#4681](https://github.com/ethers-io/ethers.js/issues/4681); [d8cb849](https://github.com/ethers-io/ethers.js/commit/d8cb84957078985f5449fa26c6fd8087dbd17aec)).
  - Added consistent timeout and cancel behaviour to FetchRequest ([#4122](https://github.com/ethers-io/ethers.js/issues/4122); [a12a739](https://github.com/ethers-io/ethers.js/commit/a12a7391fba39b5c114fa658590fae305dcedd17)).

ethers/v6.12.2 (2024-05-30 17:24)
---------------------------------

  - Copy EIP-4844 properties during estimateGas and call ([#4728](https://github.com/ethers-io/ethers.js/issues/4728); [cebe5ee](https://github.com/ethers-io/ethers.js/commit/cebe5eed91de0db5931b7847e76ee27cb2ce9219)).
  - Use non-capturing regex for data to prevent memory exhaustion for long strings ([#4741](https://github.com/ethers-io/ethers.js/issues/4741); [5463aa0](https://github.com/ethers-io/ethers.js/commit/5463aa03eacde45322a1e05693ce90e4d7abcaa7)).
  - Added Base endpointsto EtherscanProvider ([#4729](https://github.com/ethers-io/ethers.js/issues/4729); [7e1dc95](https://github.com/ethers-io/ethers.js/commit/7e1dc95ea2564c1eb0a9452b9a16002f3696765c)).

ethers/v6.12.1 (2024-04-30 22:46)
---------------------------------

  - Prevent bad Interface clone when using two different versions of v6 ([#4689](https://github.com/ethers-io/ethers.js/issues/4689); [4d2d90f](https://github.com/ethers-io/ethers.js/commit/4d2d90f5cea2eb2f9559e490a34aa1567c8c4c14)).
  - Fixed typo in error message for invalid quorum weight ([#4149](https://github.com/ethers-io/ethers.js/issues/4149); [45b9b9c](https://github.com/ethers-io/ethers.js/commit/45b9b9c9322bf20feaf892d948bcfb8db8932877)).
  - Added matic-amoy to EtherescanProvider ([#4711](https://github.com/ethers-io/ethers.js/issues/4711); [5c8d17a](https://github.com/ethers-io/ethers.js/commit/5c8d17a61825fe002bd45ee5b2239bfd8c8ae189)).
  - Fix JsonRpcProvider ignoring pollingInterval in options ([#4644](https://github.com/ethers-io/ethers.js/issues/4644); [7b7be0d](https://github.com/ethers-io/ethers.js/commit/7b7be0d1ef637f073b28bce54f4ecdfb8c88d09c)).

ethers/v6.12.0 (2024-04-17 01:09)
---------------------------------

  - Added Linea Sepolia network and Infura endpoint ([#4655](https://github.com/ethers-io/ethers.js/issues/4655); [b4aaab8](https://github.com/ethers-io/ethers.js/commit/b4aaab8d39fe47f8a1a296fa442f0856f84faf03)).
  - Do not send unsubscribe messages to destroyed Providers ([#4678](https://github.com/ethers-io/ethers.js/issues/4678); [c45935e](https://github.com/ethers-io/ethers.js/commit/c45935e29ca0dd1ecdf1277fa1107246041be580)).
  - Get definitive network from InfuraProvider when using InfuraWebSocketProvider ([38e32d8](https://github.com/ethers-io/ethers.js/commit/38e32d82145eb289e5179f9b6b11f4a9225a7022)).
  - Better error messages for transaction field mismatch ([#4659](https://github.com/ethers-io/ethers.js/issues/4659); [9230aa0](https://github.com/ethers-io/ethers.js/commit/9230aa0b9a88b5241915a8d6afa8a522d35abd5d)).
  - Added prevRandao to block ([#3372](https://github.com/ethers-io/ethers.js/issues/3372); [ec6a754](https://github.com/ethers-io/ethers.js/commit/ec6a754f0c8647dae59c73b2589225cb200d83dd)).
  - Added Polygon Amoy testnet ([#4645](https://github.com/ethers-io/ethers.js/issues/4645); [1717abb](https://github.com/ethers-io/ethers.js/commit/1717abbf29a14a6f6b106e479fe9a5b1f8768dc4)).
  - Added Chainstack provider ([#2741](https://github.com/ethers-io/ethers.js/issues/2741); [014004d](https://github.com/ethers-io/ethers.js/commit/014004d9402d7fd8c15553792cfb7a8a84ed327a)).
  - Added deep conversion to Result for toObject and toArray ([#4681](https://github.com/ethers-io/ethers.js/issues/4681); [03bfe2a](https://github.com/ethers-io/ethers.js/commit/03bfe2a4f7b29b15cd90127974b7fc1d8b03edf9)).
  - Added EIP-4844 broadcast support ([92bad88](https://github.com/ethers-io/ethers.js/commit/92bad88261a5d8a538535a7d5528162fe5010527)).
  - Fix ignored throttle parameters ([#4663](https://github.com/ethers-io/ethers.js/issues/4663); [12772e9](https://github.com/ethers-io/ethers.js/commit/12772e9498b70f8538838f30e16f3792ea90e173)).

ethers/v6.11.1 (2024-02-14 13:13)
---------------------------------

  - Throw an error when attempting to derive from a master path from a non-master node ([#4551](https://github.com/ethers-io/ethers.js/issues/4551); [556fdd9](https://github.com/ethers-io/ethers.js/commit/556fdd91d9b6bf7db4041bb099e66b2080e1a985)).
  - Allow ENS wildcards with labels up to 255 bytes wide; discussed with ENS and deemed safe ([#4543](https://github.com/ethers-io/ethers.js/issues/4543); [7f14bde](https://github.com/ethers-io/ethers.js/commit/7f14bdebf1aef6760462a1c2437c31f002b984fe)).
  - Enforce string is passed to toUtf8Bytes ([#4583](https://github.com/ethers-io/ethers.js/issues/4583); [f45bb87](https://github.com/ethers-io/ethers.js/commit/f45bb87aefaf2c6c3a4991f6e30a81c227ae83c0)).
  - Fix transaction.index not being populated on some backends ([#4591](https://github.com/ethers-io/ethers.js/issues/4591); [7f0e140](https://github.com/ethers-io/ethers.js/commit/7f0e140d5e3925a42e8bb2ac9eb1ba3fbd939864)).

ethers/v6.11.0 (2024-02-08 20:26)
---------------------------------

  - Allow transaction encoding for inferred type transactions ([f02211d](https://github.com/ethers-io/ethers.js/commit/f02211d055567b51373b5faa2c3dc6efe0523618)).
  - Added EIP-4788, receipts root and state root fields to Block ([#4570](https://github.com/ethers-io/ethers.js/issues/4570); [c5f126f](https://github.com/ethers-io/ethers.js/commit/c5f126faf7d826b6a99df0ee578ff3d0ef409381)).
  - Added EIP-4844 fields to Provider classes and formatter ([#4570](https://github.com/ethers-io/ethers.js/issues/4570); [7b4f2c1](https://github.com/ethers-io/ethers.js/commit/7b4f2c1a74db411829b5e8ef758bfa2ee21e5890)).
  - Assert BrowserProvider receives an EIP-1193 provider to fail early when passing undefined ethereum object ([b69f43b](https://github.com/ethers-io/ethers.js/commit/b69f43bc6f35da881ca7a0c8ccc5fda92edd076d)).
  - Add timeout to ContractTransactionResponse wait ([#4497](https://github.com/ethers-io/ethers.js/issues/4497); [095de51](https://github.com/ethers-io/ethers.js/commit/095de51e605a9b88576e5e34fd55a6e32befa4eb)).
  - Allow override keyword in human-readable ABI and improve error messages ([#4514](https://github.com/ethers-io/ethers.js/issues/4514), [#4548](https://github.com/ethers-io/ethers.js/issues/4548); [be5ec2d](https://github.com/ethers-io/ethers.js/commit/be5ec2d327a503b2e5fc0f37c47eee9e828f8e23)).
  - Expand Contract sub-class to accept BaseContract super-class constructor arguments ([#4538](https://github.com/ethers-io/ethers.js/issues/4538); [98496bc](https://github.com/ethers-io/ethers.js/commit/98496bc48ec23ce0d9c21d3c6c87e5b1b796a610)).
  - Allow network for default provider to be null to select mainnet ([#4501](https://github.com/ethers-io/ethers.js/issues/4501); [b6bf7ab](https://github.com/ethers-io/ethers.js/commit/b6bf7aba62fb38839cd01858432b801cc5c28a11)).
  - Allow long dnsEncode names with optional length parameter ([#4543](https://github.com/ethers-io/ethers.js/issues/4543); [a136348](https://github.com/ethers-io/ethers.js/commit/a1363483a56b0dee342595c8f44ed8fcce7ecca9)).
  - Fix parseLog signature when receiving read-only array for topics ([#4029](https://github.com/ethers-io/ethers.js/issues/4029), [#4459](https://github.com/ethers-io/ethers.js/issues/4459); [20cd8a2](https://github.com/ethers-io/ethers.js/commit/20cd8a23eaf8e8a14e2b51f7f64da4cb3e32fccb)).
  - Use Secure endpoints for BNB on Etherscan ([#4525](https://github.com/ethers-io/ethers.js/issues/4525); [1f6e188](https://github.com/ethers-io/ethers.js/commit/1f6e1882515195bd67f0bce9fe347ec05107324b)).
  - Added holesky network and related end-points for supporting providers ([c6e6c43](https://github.com/ethers-io/ethers.js/commit/c6e6c432574a0b7e55c300ab3e470aafdace28b3)).
  - Added EIP-4844 BLOb transactions ([#4554](https://github.com/ethers-io/ethers.js/issues/4554); [9c1e82e](https://github.com/ethers-io/ethers.js/commit/9c1e82e1230526ebcd62902890c4f24b1f7f7d79)).
  - Normalize EIP-712 types before computing the payload ([#4541](https://github.com/ethers-io/ethers.js/issues/4541); [56c1361](https://github.com/ethers-io/ethers.js/commit/56c1361ee83db8b68859caf0850c95ff70e7e306)).
  - Updated thrid-part provider URLs for QuickNode ([2b4891d](https://github.com/ethers-io/ethers.js/commit/2b4891d86e72e849079cb1dc98b18e158b0c0620)).
  - Fixed normalization and abstracted EIP-712 Array parsing ([#4541](https://github.com/ethers-io/ethers.js/issues/4541); [8f99601](https://github.com/ethers-io/ethers.js/commit/8f99601df1f26a8ba4d6d9dea5e033e7f688107e)).
  - Updated third-party provider network URLs ([#4542](https://github.com/ethers-io/ethers.js/issues/4542); [84ca14f](https://github.com/ethers-io/ethers.js/commit/84ca14f1ffc5afbdd7f4c26a9b734ec5951eee3c)).
  - Added additional sepolia testnets ([4efef76](https://github.com/ethers-io/ethers.js/commit/4efef76e8cab0acaf1b2ba231a0148f9381bb1ee)).
  - Fix EIP-712 type aliases for uint and int ([#4541](https://github.com/ethers-io/ethers.js/issues/4541); [43fb9c2](https://github.com/ethers-io/ethers.js/commit/43fb9c233696aeaa80b1c2b0e5fafce90e0ad508)).
  - Fixed typo in Error string ([#4539](https://github.com/ethers-io/ethers.js/issues/4539); [7882905](https://github.com/ethers-io/ethers.js/commit/78829050853093bc5291ae78fc5a904044759aa0)).
  - Better debugging output on fetch errors ([bee07a0](https://github.com/ethers-io/ethers.js/commit/bee07a0750b448a9d13c2d57014bcf27f43e2ed7)).

ethers/v6.10.0 (2024-01-12 19:46)
---------------------------------

  - Limit decoded result imflation ratio from ABI-encoded data ([#4537](https://github.com/ethers-io/ethers.js/issues/4537); [1b4debd](https://github.com/ethers-io/ethers.js/commit/1b4debd4a9e61d171bfc60590116facb8bdbd2da)).

ethers/v6.9.2 (2024-01-02 19:12)
--------------------------------

  - Fix Base58 padding for string representation of binary data ([#4527](https://github.com/ethers-io/ethers.js/issues/4527); [ccac24a](https://github.com/ethers-io/ethers.js/commit/ccac24a5b0a4d07a4b639c1c4d0a44703e32d418)).

ethers/v6.9.1 (2023-12-19 04:53)
--------------------------------

  - Fix uncatchable issue when sending transactions over JSON-RPC and provide some retry-recovery for missing v ([#4513](https://github.com/ethers-io/ethers.js/issues/4513); [1802215](https://github.com/ethers-io/ethers.js/commit/180221574c5d2af9ad85404af4fab8752d3d5029)).

ethers/v6.9.0 (2023-11-27 06:15)
--------------------------------

  - Use provider-specified suggested priority fee when available, otherwise fallback onto existing logic of 1 gwei ([#4463](https://github.com/ethers-io/ethers.js/issues/4463); [f8f11c7](https://github.com/ethers-io/ethers.js/commit/f8f11c754aa2c9b541db73d3bde66a8ffa5146f0)).
  - Add auto-detected static network support to providers and allow customizing socket provider options ([#4199](https://github.com/ethers-io/ethers.js/issues/4199), [#4418](https://github.com/ethers-io/ethers.js/issues/4418), [#4441](https://github.com/ethers-io/ethers.js/issues/4441); [4681b83](https://github.com/ethers-io/ethers.js/commit/4681b83d516ab2eb41ddb68b5021c97e14c6f2cf)).
  - Added Base network to AlchemyProvider ([#4384](https://github.com/ethers-io/ethers.js/issues/4384); [9e74d14](https://github.com/ethers-io/ethers.js/commit/9e74d14432e6efebdff21b9a7d2e6143af55e143)).
  - Fixed ParamType formatting causing bad tuple full and minimal ABI output ([#4329](https://github.com/ethers-io/ethers.js/issues/4329), [#4479](https://github.com/ethers-io/ethers.js/issues/4479); [2b67488](https://github.com/ethers-io/ethers.js/commit/2b6748815169abf2c99a647131875c13b8b6a787)).
  - Adjust for provider config weight when kicking off a request in FallbackProvider ([#4298](https://github.com/ethers-io/ethers.js/issues/4298); [da34e35](https://github.com/ethers-io/ethers.js/commit/da34e3569e95357d9469209d926cb645f0750bfa)).
  - More robust FallbackProvider broadcast ([#4186](https://github.com/ethers-io/ethers.js/issues/4186), [#4297](https://github.com/ethers-io/ethers.js/issues/4297), [#4442](https://github.com/ethers-io/ethers.js/issues/4442); [e2485b8](https://github.com/ethers-io/ethers.js/commit/e2485b8ef927d18c7a15d2d29b3b0feffec9991a)).
  - Added safe and finalized provider events ([#3921](https://github.com/ethers-io/ethers.js/issues/3921); [a92766e](https://github.com/ethers-io/ethers.js/commit/a92766e56ad04185625037d84fc28adaac7fae8c)).

ethers/v6.8.1 (2023-11-01 16:08)
--------------------------------

  - Fixed typo in error description when converting values to arrays ([#4427](https://github.com/ethers-io/ethers.js/issues/4427), [#4446](https://github.com/ethers-io/ethers.js/issues/4446); [8fed2f8](https://github.com/ethers-io/ethers.js/commit/8fed2f84768ace4bf3e5742c931a74841da7c637)).
  - Fix invalid token nonpayable being included in formatted constructor ([#4412](https://github.com/ethers-io/ethers.js/issues/4412); [2e0bd90](https://github.com/ethers-io/ethers.js/commit/2e0bd90744b8e76fcf03f75a66cb0061d50f7bd9)).
  - Add ENS support for Sepolia ([#4422](https://github.com/ethers-io/ethers.js/issues/4422); [1da50ae](https://github.com/ethers-io/ethers.js/commit/1da50ae286da01e58a70bb8df8aa5cc5d260e33e)).

ethers/v6.8.0 (2023-10-10 22:42)
--------------------------------

  - Replicated former ENS normalize behaviour for empty strings and update namehash testcases ([125ff11](https://github.com/ethers-io/ethers.js/commit/125ff1189b9cefb8abfd7da9c104c75e382a50cc)).
  - Initial shortMessage support for errors ([#4241](https://github.com/ethers-io/ethers.js/issues/4241); [d6a8c14](https://github.com/ethers-io/ethers.js/commit/d6a8c14d907cf8b90347444c0186b83a5db2e293)).
  - Fixed resolving ENS addresses used as from parameters ([#3961](https://github.com/ethers-io/ethers.js/issues/3961); [2616f4c](https://github.com/ethers-io/ethers.js/commit/2616f4c30c82bd45449b73fa37ef269d60a07d80)).
  - Merge: 9a4b7534 0c9c23b0     Merge branch 'v5.8-progress' ([cd5f0fe](https://github.com/ethers-io/ethers.js/commit/cd5f0fe03f2137fbc47e295f8db38a5151111e72)).
  - Allow more loose input format for RLP encoder ([#4402](https://github.com/ethers-io/ethers.js/issues/4402); [9a4b753](https://github.com/ethers-io/ethers.js/commit/9a4b7534458fc79a0654b0eb57fc956bffa02a2f)).
  - Update to latest noble crypto libraries ([#3975](https://github.com/ethers-io/ethers.js/issues/3975); [b27faa0](https://github.com/ethers-io/ethers.js/commit/b27faa02ac8f90e2e54b188e8139c59d98c469e3)).
  - More robust configuration options for FetchRequest getUrl functions ([#4353](https://github.com/ethers-io/ethers.js/issues/4353); [9541f2f](https://github.com/ethers-io/ethers.js/commit/9541f2f70cd7f5c6f3caf93f5a3d5e34eae5281a)).
  - Ignore blockTag when calling Etherscan if it is the default block tag ([dcea9b3](https://github.com/ethers-io/ethers.js/commit/dcea9b353619d85878ad2ba340ae17e5c285d558)).

ethers/v6.7.1 (2023-08-15 03:08)
--------------------------------

  - Prevent destroyed providers from emitting network detection errors ([7d41730](https://github.com/ethers-io/ethers.js/commit/7d4173049edc3b4ff2de1971c3ecca3b08588651)).
  - Fix VSCode reported lint issues ([#4153](https://github.com/ethers-io/ethers.js/issues/4153), [#4156](https://github.com/ethers-io/ethers.js/issues/4156), [#4158](https://github.com/ethers-io/ethers.js/issues/4158), [#4159](https://github.com/ethers-io/ethers.js/issues/4159); [4eb84da](https://github.com/ethers-io/ethers.js/commit/4eb84da865a82a27c5113c38102b6b710096958e), [203dfc3](https://github.com/ethers-io/ethers.js/commit/203dfc33b9c8e72c9cdfe0a349ac763ef17a4484)).
  - Add gasPrice to Polygon feeData for type 0 and type 1 legacy transactions ([#4315](https://github.com/ethers-io/ethers.js/issues/4315); [0df3ab9](https://github.com/ethers-io/ethers.js/commit/0df3ab93137039de1e1986bbfe9a5b32ceffa8a4)).

ethers/v6.7.0 (2023-08-02 23:52)
--------------------------------

  - Fixed receipt wait not throwing on reverted transactions ([25fef4f](https://github.com/ethers-io/ethers.js/commit/25fef4f8d756f5bbf5a2a05e38233248a8eb43ac)).
  - Added custom priority fee to Optimism chain (via telegram) ([ff80b04](https://github.com/ethers-io/ethers.js/commit/ff80b04f31da21496e72d3687cecd1c01efaecc5)).
  - Add context to Logs that fail decoding due to ABI issues to help debugging ([f3c46f2](https://github.com/ethers-io/ethers.js/commit/f3c46f22994d194ff78b3b176407b2ecb7af1c77)).
  - Added new exports for FallbackProviderOptions and FetchUrlFeeDataNetworkPlugin ([#2828](https://github.com/ethers-io/ethers.js/issues/2828), [#4160](https://github.com/ethers-io/ethers.js/issues/4160); [b1dbbb0](https://github.com/ethers-io/ethers.js/commit/b1dbbb0de3f10a3d9e12d6a84ad5c52bea25c7f6)).
  - Allow overriding pollingInterval in JsonRpcProvider constructor (via discord) ([f42f258](https://github.com/ethers-io/ethers.js/commit/f42f258beb305a06e563ad16522f095a72da32eb)).
  - Fixed FallbackProvider priority sorting ([#4150](https://github.com/ethers-io/ethers.js/issues/4150); [78538eb](https://github.com/ethers-io/ethers.js/commit/78538eb100addd135d29e60c9fa4fed3946278fa)).
  - Added linea network to InfuraProvider and Network ([#4184](https://github.com/ethers-io/ethers.js/issues/4184), [#4190](https://github.com/ethers-io/ethers.js/issues/4190); [d3e5e2c](https://github.com/ethers-io/ethers.js/commit/d3e5e2c45b28c377f306091acfc024e30c49ef20)).
  - Added whitelist support to getDefaultProvider ([82bb936](https://github.com/ethers-io/ethers.js/commit/82bb936542e29c6441ac8dc2d3ebbdd4edb708ee)).
  - Add Polygon RPC endpoints to the default provider ([#3689](https://github.com/ethers-io/ethers.js/issues/3689); [23704a9](https://github.com/ethers-io/ethers.js/commit/23704a9c44d5857817e138fb19d44ce2103ca005)).
  - Added customizable quorum to FallbackProvider ([#4160](https://github.com/ethers-io/ethers.js/issues/4160); [8f0a509](https://github.com/ethers-io/ethers.js/commit/8f0a50921a12a866addcf5b0fabc576bfc287689)).
  - Added basic Gas Station support via a NetworkPlugin ([#2828](https://github.com/ethers-io/ethers.js/issues/2828); [229145d](https://github.com/ethers-io/ethers.js/commit/229145ddf566a962517588eaeed155734c7d4598)).
  - Add BNB URLs to EtherscanProvider networks ([ec39abe](https://github.com/ethers-io/ethers.js/commit/ec39abe067259fad4ea8607a6c5aece61890eb41)).
  - Added tests for JSON format ([#4248](https://github.com/ethers-io/ethers.js/issues/4248); [ba36079](https://github.com/ethers-io/ethers.js/commit/ba36079a285706694532ce726568c4c447acad47)).
  - Use empty string for unnamed parameters in JSON output instead of undefined ([#4248](https://github.com/ethers-io/ethers.js/issues/4248); [8c2652c](https://github.com/ethers-io/ethers.js/commit/8c2652c8cb4d054207d89688d30930869d9d3f8b)).
  - Return undefined for Contract properties that do not exist instead of throwing an error ([#4266](https://github.com/ethers-io/ethers.js/issues/4266); [5bf7b34](https://github.com/ethers-io/ethers.js/commit/5bf7b3494ed62952fc387b4368a0bdc86dfe163e)).

ethers/v6.6.7 (2023-07-28 14:50)
--------------------------------

  - Prevent malformed logs from preventing other logs being decoded ([#4275](https://github.com/ethers-io/ethers.js/issues/4275); [0dca645](https://github.com/ethers-io/ethers.js/commit/0dca645632d73488bf6ad460e0d779361a537bbe)).
  - Allow visibility on human-readable constructors ([#4278](https://github.com/ethers-io/ethers.js/issues/4278); [3a52201](https://github.com/ethers-io/ethers.js/commit/3a52201fe2ba68a00105cca2c0901da5ffa18d6b)).

ethers/v6.6.6 (2023-07-28 01:14)
--------------------------------

  - Better error message when passing invalid overrides object into a contract deployment ([#4182](https://github.com/ethers-io/ethers.js/issues/4182); [aa2ea3d](https://github.com/ethers-io/ethers.js/commit/aa2ea3d5296956fd0d40b83888e1ca053bb250ee)).

ethers/v6.6.5 (2023-07-24 00:04)
--------------------------------

  - Reflect symbols in the Contract Proxy to target ([#4084](https://github.com/ethers-io/ethers.js/issues/4048); [ac2f5e5](https://github.com/ethers-io/ethers.js/commit/ac2f5e563b8ec0e91a931470eb6ea58b0c01fb3d)).
  - Allow arrays of address for indexed filter topics ([#4259](https://github.com/ethers-io/ethers.js/issues/4259); [93af87c](https://github.com/ethers-io/ethers.js/commit/93af87c447eeb77090e29bd940612603b3f74026)).
  - Fixed filter encoding for bytesX ([#4244](https://github.com/ethers-io/ethers.js/issues/4244); [fa3a883](https://github.com/ethers-io/ethers.js/commit/fa3a883ff7c88611ce766f58bdd4b8ac90814470)).
  - Fix JSON formatting for tuple arrays ([#4237](https://github.com/ethers-io/ethers.js/issues/4237); [a8bc49b](https://github.com/ethers-io/ethers.js/commit/a8bc49bdcf07a51b35f38cf209db27e116cc1a59)).
  - Better error messages when parsing fragment strings ([#4246](https://github.com/ethers-io/ethers.js/issues/4246); [e36b6c3](https://github.com/ethers-io/ethers.js/commit/e36b6c35b7bc777c9adbe0055b32b31a13185240)).
  - Include the missing fragment key and args when no matching Contract method or event is present ([#3809](https://github.com/ethers-io/ethers.js/issues/3809); [450a176](https://github.com/ethers-io/ethers.js/commit/450a176ee25f88a2ddb9ff23b153ef70bf1dc546)).
  - Prevent a single malformed event from preventing other Contract logs; reported on Discord ([b1375f4](https://github.com/ethers-io/ethers.js/commit/b1375f4e4463b856855ebc684b45945455ac082e)).

ethers/v6.6.4 (2023-07-16 00:35)
--------------------------------

  - More robust support for Signatures with less standard parameter values ([#3835](https://github.com/ethers-io/ethers.js/issues/3835), [#4228](https://github.com/ethers-io/ethers.js/issues/4228); [a7e4048](https://github.com/ethers-io/ethers.js/commit/a7e4048fe3b75a743cec8c8ef2a5fad4bdc8b14c)).
  - Fixed CCIP-read in the EnsResolver ([#4221](https://github.com/ethers-io/ethers.js/issues/4221); [57f1e1c](https://github.com/ethers-io/ethers.js/commit/57f1e1c47148921148e35c10c83539531942923e)).
  - Skip checking confirmation count if confirms is 0 ([#4229](https://github.com/ethers-io/ethers.js/issues/4229), [#4242](https://github.com/ethers-io/ethers.js/issues/4242); [492919d](https://github.com/ethers-io/ethers.js/commit/492919d14f646c630f29e1596e5564df1e51f309)).
  - Fixed waiting for confirmations in deployment transactions ([#4212](https://github.com/ethers-io/ethers.js/issues/4212), [#4230](https://github.com/ethers-io/ethers.js/issues/4230); [43c253a](https://github.com/ethers-io/ethers.js/commit/43c253a402f52a08353c424f6c4e236836cfaf36)).

ethers/v6.6.3 (2023-07-11 20:55)
--------------------------------

  - Throw more descriptive error for unconfigured ENS name contract targets ([#4213](https://github.com/ethers-io/ethers.js/issues/4213); [80f62ef](https://github.com/ethers-io/ethers.js/commit/80f62efc41c3a29e690af40a1976928b7f886a0e)).
  - Fixed contract once not running stop callback ([7d061b7](https://github.com/ethers-io/ethers.js/commit/7d061b786f72cbfc461bf80d139d10aeff533a6e)).

ethers/v6.6.2 (2023-06-27 23:30)
--------------------------------

  - Wider error detection for call exceptions on certain backends ([#4154](https://github.com/ethers-io/ethers.js/issues/4154), [#4155](https://github.com/ethers-io/ethers.js/issues/4155); [9197f9f](https://github.com/ethers-io/ethers.js/commit/9197f9f938b5f3b5f97c043f2dab06854656c932)).
  - Added wider error deetection for JSON-RPC unsupported operation ([#4162](https://github.com/ethers-io/ethers.js/issues/4162); [1dc8986](https://github.com/ethers-io/ethers.js/commit/1dc8986a33be9dce536b24189326cbfaabf1342e)).
  - Fixed formatUnits and parseUnits for values over 128 bits ([#4037](https://github.com/ethers-io/ethers.js/issues/4037), [#4133](https://github.com/ethers-io/ethers.js/issues/4133); [3d141b4](https://github.com/ethers-io/ethers.js/commit/3d141b44b528f52b3c9205125b64ce342f91643c)).

ethers/v6.6.1 (2023-06-23 00:35)
--------------------------------

  - Fixed CCIP read in contract calls ([#4043](https://github.com/ethers-io/ethers.js/issues/4043); [d51e3fb](https://github.com/ethers-io/ethers.js/commit/d51e3fbff43c31d88353ac71151626312d22c0b9), [857aa8c](https://github.com/ethers-io/ethers.js/commit/857aa8ccc30f25eda8e83dcac3e0ad2c1a5ce2b3)).

ethers/v6.6.0 (2023-06-13 21:42)
--------------------------------

  - Add exports for AbstractProviderOptions and for MulticoinProviderPlugin ([203a759](https://github.com/ethers-io/ethers.js/commit/203a759efc65bf6901d3e574a601525ea3936238)).
  - Add option to adjust perform cache timeout in AbstractProvider ([de0f518](https://github.com/ethers-io/ethers.js/commit/de0f5189f695c181a5fa09100af96a691a338e2b)).
  - Add full support for MultiCoin plugins and automatic detection for EVM-compatible coin types ([#3888](https://github.com/ethers-io/ethers.js/issues/3888), [#4081](https://github.com/ethers-io/ethers.js/issues/4081); [84375be](https://github.com/ethers-io/ethers.js/commit/84375be92d32a2939cf4a2f713e4c554b5b54a32)).
  - Allow Interface instances where InterfaceAbi are allowed ([#4142](https://github.com/ethers-io/ethers.js/issues/4142); [2318005](https://github.com/ethers-io/ethers.js/commit/2318005dfd996c8a7c51603d0264ceabe9bb6141)).
  - Allow Numeric type for decimals in FixedNumber ([#4141](https://github.com/ethers-io/ethers.js/issues/4141); [9055ef6](https://github.com/ethers-io/ethers.js/commit/9055ef6c69291f1a44ea23a2e7b5aaf3140a5577)).

ethers/v6.5.1 (2023-06-07 20:19)
--------------------------------

  - Fix lost promise fulfillment when a batch has an error response ([#4126](https://github.com/ethers-io/ethers.js/issues/4126); [8dd21f0](https://github.com/ethers-io/ethers.js/commit/8dd21f03334ffd3cdb7ac532376d51fd4130c7ab)).

ethers/v6.5.0 (2023-06-06 22:41)
--------------------------------

  - Fix CJS browser bundling ([#4033](https://github.com/ethers-io/ethers.js/issues/4033); [38ee319](https://github.com/ethers-io/ethers.js/commit/38ee3195b0192d8180899fd61308e03fa3a0eb32)).
  - Fixed type guard for non-Typed instances ([#4087](https://github.com/ethers-io/ethers.js/issues/4087); [20c3d1b](https://github.com/ethers-io/ethers.js/commit/20c3d1b109743e33ab60a75d69bf7ede73b15ce2)).
  - Add confirmations to TransactionResponse ([#4094](https://github.com/ethers-io/ethers.js/issues/4094); [bb8685b](https://github.com/ethers-io/ethers.js/commit/bb8685b112ce1c689c740d4dbcb358c16fb9b22d)).
  - Fix stray promises when a node returns invalid results ([#4118](https://github.com/ethers-io/ethers.js/issues/4118); [3c1bad2](https://github.com/ethers-io/ethers.js/commit/3c1bad2fb7ad4a6ff90ff11f3e382fd18e41c800)).
  - Added support to detect and stop providers spinning on intitial network detection ([#4015](https://github.com/ethers-io/ethers.js/issues/4015); [f37a52d](https://github.com/ethers-io/ethers.js/commit/f37a52da28ac130b7f4de52901618320994ea87a)).

ethers/v6.4.2 (2023-06-05 22:41)
--------------------------------

  - Bump ens-normalize version ([#4071](https://github.com/ethers-io/ethers.js/issues/4071), [#4077](https://github.com/ethers-io/ethers.js/issues/4077), [#4080](https://github.com/ethers-io/ethers.js/issues/4080), [#4102](https://github.com/ethers-io/ethers.js/issues/4102); [c135784](https://github.com/ethers-io/ethers.js/commit/c1357847dcdec93d72f28d890f9271d0289ccefd)).
  - Fix for networks with polling with non-consistent block and filter events ([#4119](https://github.com/ethers-io/ethers.js/issues/4119); [9b0e992](https://github.com/ethers-io/ethers.js/commit/9b0e9920c09577296ec0e2abb3acc3f3299d96c7)).

ethers/v6.4.1 (2023-06-01 17:52)
--------------------------------

  - Fixed AbstractProvider lookupAddress bug ([#4086](https://github.com/ethers-io/ethers.js/issues/4086); [15ed2f5](https://github.com/ethers-io/ethers.js/commit/15ed2f5b32084527961332481c9442a313036a01)).
  - Fix FixedNumber comparison bug ([#4112](https://github.com/ethers-io/ethers.js/issues/4112); [d8e9586](https://github.com/ethers-io/ethers.js/commit/d8e9586044e888e424b5ead0f6e01f88140dba8a)).

ethers/v6.4.0 (2023-05-18 17:28)
--------------------------------

  - Coerce value into BigInt when checking for value ([83d7f43](https://github.com/ethers-io/ethers.js/commit/83d7f43b9ca4b9868a3952510e56b41ea8610baa)).
  - Better errors when junk passed as Contract target ([#3947](https://github.com/ethers-io/ethers.js/issues/3947), [#4053](https://github.com/ethers-io/ethers.js/issues/4053); [219b16d](https://github.com/ethers-io/ethers.js/commit/219b16dc284b0c6a532c8c49e824d8234f94222b)).
  - More robust message checking in socket providers ([#4051](https://github.com/ethers-io/ethers.js/issues/4051); [f58990b](https://github.com/ethers-io/ethers.js/commit/f58990b80cfd83579014339315e58663c0aa6ae3)).
  - More robust defaultProvider start-up when a backend fails on bootstrap ([#3979](https://github.com/ethers-io/ethers.js/issues/3979); [984f6fa](https://github.com/ethers-io/ethers.js/commit/984f6fa155fca08ebec2353c75ee0a0b974e8568)).
  - Fix Result.map when Array contains zero elements ([#4036](https://github.com/ethers-io/ethers.js/issues/4036), [#4048](https://github.com/ethers-io/ethers.js/issues/4048); [2e5935b](https://github.com/ethers-io/ethers.js/commit/2e5935b91cff462165a054b33c8b8413f51e3f39)).
  - Fixed error handling for contracts with receive and non-payable fallback ([6db7458](https://github.com/ethers-io/ethers.js/commit/6db7458cf0a09e8e8a2abb712239972ab81dc9df)).
  - Remove superfluous logging in defaultProvider ([f87f6ef](https://github.com/ethers-io/ethers.js/commit/f87f6ef9a01ca399664f9fe106b0a677dba0c8e8)).
  - Removed superfluous logging ([1bc8b55](https://github.com/ethers-io/ethers.js/commit/1bc8b55d502a95c4ae58352bdcfce9e5f9ea72d3)).
  - Fix receipt gas price when effectiveGasPrice is 0 on testnets ([#4014](https://github.com/ethers-io/ethers.js/issues/4014); [2b0fe61](https://github.com/ethers-io/ethers.js/commit/2b0fe611335432aee334d777a64d8c7827881618)).
  - Added error event to provider ([#3970](https://github.com/ethers-io/ethers.js/issues/3970), [#3982](https://github.com/ethers-io/ethers.js/issues/3982); [af0291c](https://github.com/ethers-io/ethers.js/commit/af0291c01639674658f5049343da88a84da763a1)).
  - Removed superfluous parameters for internal transaction functions ([e848978](https://github.com/ethers-io/ethers.js/commit/e8489787585c2e69a23f6cdec6901f22b096aebe)).
  - More aggresive tree-shaking ([076edad](https://github.com/ethers-io/ethers.js/commit/076edad81ef62474f48f2b4c8af0edc6e4fd64f2)).
  - More flexible static network checking ([#3834](https://github.com/ethers-io/ethers.js/issues/3834); [7c0465c](https://github.com/ethers-io/ethers.js/commit/7c0465c5fb834eba18d4e5535072685bdc1029f0)).
  - Support transitive dependants that use non-node16 moduleResolution ([#3920](https://github.com/ethers-io/ethers.js/issues/3920); [df685b1](https://github.com/ethers-io/ethers.js/commit/df685b1bd9ad346ee7863beb6c3ca3f4e94932a2)).
  - Populate any missing log.removed with false ([#3959](https://github.com/ethers-io/ethers.js/issues/3959); [4e478e6](https://github.com/ethers-io/ethers.js/commit/4e478e625d5648f2172631eef5fda5776ee776b0)).

ethers/v6.3.0 (2023-04-06 04:35)
--------------------------------

  - Added support for legacy ABI JSON fragments ([#3932](https://github.com/ethers-io/ethers.js/issues/3932); [8c5973e](https://github.com/ethers-io/ethers.js/commit/8c5973e3a9b8d4d4ed80bdf209d8a0b6cc6b8d6d)).
  - Add _in_ operator support for contract and contract.filters ([#3901](https://github.com/ethers-io/ethers.js/issues/3901); [c58ab3a](https://github.com/ethers-io/ethers.js/commit/c58ab3a97687e15a3ffe30b038089c5f4b570bb9)).
  - Fixed TypedData unsigned value range ([#3873](https://github.com/ethers-io/ethers.js/issues/3873); [a851b24](https://github.com/ethers-io/ethers.js/commit/a851b24d0af009ecf277766d2a5f81f9b3e7f9f8)).
  - Added missing export for getIndexedAccountPath ([#3875](https://github.com/ethers-io/ethers.js/issues/3875); [356ff2b](https://github.com/ethers-io/ethers.js/commit/356ff2becb4f4d3622b281d3825770af5caf71ca)).
  - Fixed TypedData payloads for JSON-restricted chainId field ([#3836](https://github.com/ethers-io/ethers.js/issues/3836); [50b74b8](https://github.com/ethers-io/ethers.js/commit/50b74b8806ef2064f2764b09f89c7ac75fda3a3c)).

ethers/v6.2.3 (2023-03-27 21:22)
--------------------------------

  - Fixed events when emitted in WebSocketProvider ([#3767](https://github.com/ethers-io/ethers.js/issues/3767), [#3922](https://github.com/ethers-io/ethers.js/issues/3922); [ffaafc0](https://github.com/ethers-io/ethers.js/commit/ffaafc0ce1cf40d1d76d8d814c9c445057bf6989)).

ethers/v6.2.2 (2023-03-24 00:49)
--------------------------------

  - Fixed FetchRequest when using credentials ([#3897](https://github.com/ethers-io/ethers.js/issues/3897); [88e8124](https://github.com/ethers-io/ethers.js/commit/88e8124c37d377628f9b8abdf140fc07ad06259f)).

ethers/v6.2.1 (2023-03-23 17:33)
--------------------------------

  - Stall block polling bootstrap when the network is down ([#3924](https://github.com/ethers-io/ethers.js/issues/3924); [603d474](https://github.com/ethers-io/ethers.js/commit/603d47496e2b667c15b72f315261d6e299381848)).

ethers/v6.2.0 (2023-03-20 15:53)
--------------------------------

  - Added extra details in the error info field for RPC errors ([30ffa78](https://github.com/ethers-io/ethers.js/commit/30ffa78d1441fa033677fa09237fc135a314f373)).
  - Remove Ankr as a default for now as the provided API key is failing ([6e01e54](https://github.com/ethers-io/ethers.js/commit/6e01e5448f4a3e2d30288d4c8447db295c3a2e7a)).
  - Fixed deferred filters after unsafe-eval changes ([#3749](https://github.com/ethers-io/ethers.js/issues/3749), [#3763](https://github.com/ethers-io/ethers.js/issues/3763); [2e3802a](https://github.com/ethers-io/ethers.js/commit/2e3802a83b8ad2f5a6269d79fbd1c83c9f2d1047)).
  - Remove use of Function sub-class to address unsafe-eval issues ([#3749](https://github.com/ethers-io/ethers.js/issues/3749), [#3763](https://github.com/ethers-io/ethers.js/issues/3763); [7d3af51](https://github.com/ethers-io/ethers.js/commit/7d3af512c75b4c24027ec2daef1e9f4c1064194a)).
  - Added verifyTypedData utility (reported on Farcaster) ([f06a445](https://github.com/ethers-io/ethers.js/commit/f06a445247f3b294f9fc805cc8fe0752accb8edc)).
  - Removed stray logging in IpcProvider ([#3908](https://github.com/ethers-io/ethers.js/issues/3908), [#3909](https://github.com/ethers-io/ethers.js/issues/3909); [e11d4c1](https://github.com/ethers-io/ethers.js/commit/e11d4c1c20cc5b6fd5803cf9636c4f5bc082dab7)).
  - Fixed legacy serialization for implicit chainId transactions ([#3898](https://github.com/ethers-io/ethers.js/issues/3898), [#3899](https://github.com/ethers-io/ethers.js/issues/3899); [fcf6c8f](https://github.com/ethers-io/ethers.js/commit/fcf6c8fcee95ec412aaafba8ec84d5049b077a4e)).
  - Fix Webpack issue (reported on discord) ([3ad4273](https://github.com/ethers-io/ethers.js/commit/3ad4273b8b714bff344ccbfb1eb71ed8a8b7cfa4)).
  - Fix some bundlers which cannot handle recursive pkg.exports ([#3848](https://github.com/ethers-io/ethers.js/issues/3848); [6315e78](https://github.com/ethers-io/ethers.js/commit/6315e78ea32147653b72ca06f6800f3e2df6ffbf)).
  - Fixed typo in signature.s error ([#3891](https://github.com/ethers-io/ethers.js/issues/3891); [47ef3eb](https://github.com/ethers-io/ethers.js/commit/47ef3ebde37bfa0c015c258c3d8a6800d751e147)).
  - Fixed stray unreachable code ([#3890](https://github.com/ethers-io/ethers.js/issues/3890); [c220fe2](https://github.com/ethers-io/ethers.js/commit/c220fe2ea747ccc80cd3c4020e0278e3daf3c4fc)).
  - Move all wrapping to proper _wrap functions ([#3818](https://github.com/ethers-io/ethers.js/issues/3818); [02a0aad](https://github.com/ethers-io/ethers.js/commit/02a0aad61212c35e8d2723a8ae589989b97dae3e)).

ethers/v6.1.0 (2023-03-07 02:10)
--------------------------------

  - Fixed ethers imported in web workers ([#3856](https://github.com/ethers-io/ethers.js/issues/3856); [5f2678f](https://github.com/ethers-io/ethers.js/commit/5f2678fb059d643638b9cc1dc59cbfc61ce7a7b8)).
  - Added Sepolia support ([#3863](https://github.com/ethers-io/ethers.js/issues/3863); [abeaa74](https://github.com/ethers-io/ethers.js/commit/abeaa74da04fbe25e837a2ffa7d1e9c1257a5da5)).
  - Added missing exports ([#3734](https://github.com/ethers-io/ethers.js/issues/3734); [06aa303](https://github.com/ethers-io/ethers.js/commit/06aa30363f88144db672376d39012d7fe3f86c33)).
  - Allow null values for TypedData domain ([#3623](https://github.com/ethers-io/ethers.js/issues/3623); [a32af3a](https://github.com/ethers-io/ethers.js/commit/a32af3adc104c4b07a45097a4a3725a4ce9e0be6)).
  - Added listAccounts to JsonRpcProvider ([#3778](https://github.com/ethers-io/ethers.js/issues/3778); [287d94f](https://github.com/ethers-io/ethers.js/commit/287d94fc454d03f1b3086ea98745131cdf40129a)).
  - Allow BigInt for blockTag ([#3780](https://github.com/ethers-io/ethers.js/issues/3780); [fe1f04c](https://github.com/ethers-io/ethers.js/commit/fe1f04c6e5fb4254a100f492d7dcbdc3cf19a446)).
  - Fixed typo in error messages ([#3822](https://github.com/ethers-io/ethers.js/issues/3822), [#3824](https://github.com/ethers-io/ethers.js/issues/3824); [f1a810d](https://github.com/ethers-io/ethers.js/commit/f1a810dcb56df54b1e1567f2a59c73500619472f)).
  - Re-adding definition files to require exports ([#3703](https://github.com/ethers-io/ethers.js/issues/3703); [76fab92](https://github.com/ethers-io/ethers.js/commit/76fab923da33e71e6bb751bb0b5e3ba3faa27ab2)).

ethers/v6.0.8 (2023-02-23 06:30)
--------------------------------

  - Fix matic-mumbai network and include aliases to legacy names ([#3811](https://github.com/ethers-io/ethers.js/issues/3811); [20bbd12](https://github.com/ethers-io/ethers.js/commit/20bbd1281911d31b360f6f5032251c9257943541)).
  - Fixed getSigner bug ([#3821](https://github.com/ethers-io/ethers.js/issues/3821); [388edf6](https://github.com/ethers-io/ethers.js/commit/388edf6abc168f89f1ca609e9e5b025dc9205add)).

ethers/v6.0.7 (2023-02-23 01:41)
--------------------------------

  - Fixed getContentHash ([#3819](https://github.com/ethers-io/ethers.js/issues/3819); [b993f7c](https://github.com/ethers-io/ethers.js/commit/b993f7c3b6c0e135c460c8b8dc5943215628231a)).

ethers/v6.0.6 (2023-02-22 21:53)
--------------------------------

  - Added chain parameters for Arbitrum and Optimism ([#3811](https://github.com/ethers-io/ethers.js/issues/3811); [77a7323](https://github.com/ethers-io/ethers.js/commit/77a7323119923e596f4def4f1bc90beae5447320)).
  - Fix NonceManager race condition ([#3812](https://github.com/ethers-io/ethers.js/issues/3812), [#3813](https://github.com/ethers-io/ethers.js/issues/3813); [5a3c10a](https://github.com/ethers-io/ethers.js/commit/5a3c10a29c047609a50828adb620d88aa8cf0014)).
  - Add UMD output to dist builds ([#3814](https://github.com/ethers-io/ethers.js/issues/3814); [f9eed4c](https://github.com/ethers-io/ethers.js/commit/f9eed4cdb190b06dd4ddaa2382c1de42e8e98de6)).

ethers/v6.0.5 (2023-02-18 22:36)
--------------------------------

  - Fixed Result to behave correctly like an array using slice and toArray ([#3787](https://github.com/ethers-io/ethers.js/issues/3787); [399356b](https://github.com/ethers-io/ethers.js/commit/399356b91227db04e496628af60c4b8e38207760)).
  - Replaced substring from 0 index with startsWith ([#3691](https://github.com/ethers-io/ethers.js/issues/3691); [4512e97](https://github.com/ethers-io/ethers.js/commit/4512e97f9b55607ce388aa6eb63a37fc196a5d9d)).
  - Fixed inverted assert in duplicate name detection for ABI encoding ([#3792](https://github.com/ethers-io/ethers.js/issues/3792); [762c2f3](https://github.com/ethers-io/ethers.js/commit/762c2f34eac848c5464389f11d1697dcd8ebcbb5)).
  - Fixed missing property during transaction copy ([#3793](https://github.com/ethers-io/ethers.js/issues/3793); [48bbef7](https://github.com/ethers-io/ethers.js/commit/48bbef7ade69bcfe86542f752f15049cc62f4141)).
  - Add support for Wallet private keys without 0x prefix ([#3768](https://github.com/ethers-io/ethers.js/issues/3768); [4665fb4](https://github.com/ethers-io/ethers.js/commit/4665fb4c6886c8b344dee316ba9f4fde57ce7557)).
  - Fixed quicknode property for defaultProvider ([#3741](https://github.com/ethers-io/ethers.js/issues/3741); [a8afb72](https://github.com/ethers-io/ethers.js/commit/a8afb72fbbceb6a5024c1edb85badb72099787ea)).
  - Fixed exports field order ([#3703](https://github.com/ethers-io/ethers.js/issues/3703), [#3755](https://github.com/ethers-io/ethers.js/issues/3755); [085a905](https://github.com/ethers-io/ethers.js/commit/085a9054f349afb816ca1a123737293ec9bd2532)).

ethers/v6.0.4 (2023-02-16 08:55)
--------------------------------

  - Fixed custom error decoding ([#3785](https://github.com/ethers-io/ethers.js/issues/3785); [4d9b29d](https://github.com/ethers-io/ethers.js/commit/4d9b29de751e2387c143e474bb96d271da892ea6)).
  - Removed stray debug logging ([e1e0929](https://github.com/ethers-io/ethers.js/commit/e1e09293483a9d07fd8e8f96552aa958b5ec45ed)).
  - Fixed lookupAddress when bad resolver is present ([#3782](https://github.com/ethers-io/ethers.js/issues/3782); [92def9c](https://github.com/ethers-io/ethers.js/commit/92def9c1489bb35ad13fe58a1cd107ee3a05a112)).
  - Fixed FallbackProvider median calculation ([#3746](https://github.com/ethers-io/ethers.js/issues/3746); [83957dc](https://github.com/ethers-io/ethers.js/commit/83957dc283043b9af8f6e89920faac3e09ca69fc)).
  - Move the xnf normalize variant to pkg.browser instead of import ([#3724](https://github.com/ethers-io/ethers.js/issues/3724); [179e6ca](https://github.com/ethers-io/ethers.js/commit/179e6ca520392177c7dea5e477b29930952ed637)).

ethers/v6.0.3 (2023-02-12 22:45)
--------------------------------

  - Allow null type in transaction receipt for legacy type 0 networks ([#3459](https://github.com/ethers-io/ethers.js/issues/3459); [6372a46](https://github.com/ethers-io/ethers.js/commit/6372a46b1b273db3e4c1189daebb4b888bd588bc)).
  - Fixed events when slicing immutable Result ([#3765](https://github.com/ethers-io/ethers.js/issues/3765); [2ba4a17](https://github.com/ethers-io/ethers.js/commit/2ba4a172555b7e17ac01fedfc944549defab61bc)).
  - More robust support on networks which throw when filters are not supported ([#3767](https://github.com/ethers-io/ethers.js/issues/3767); [37bf4fb](https://github.com/ethers-io/ethers.js/commit/37bf4fb55563d7ff66edee15c7515c8a0d6a2266)).
  - Fixed ignored polling override for JsonRpcApiProvider ([400d576](https://github.com/ethers-io/ethers.js/commit/400d57621b3e9a33679a528b5072449699f0a068)).

ethers/v6.0.2 (2023-02-04 08:50)
--------------------------------

  - Fixed crossed assert in Fetch ([#3733](https://github.com/ethers-io/ethers.js/issues/3733); [6c338c1](https://github.com/ethers-io/ethers.js/commit/6c338c1c5b4013db9754c9d1a33dcbf54330e5c7)).

ethers/v6.0.1 (2023-02-04 04:06)
--------------------------------

  - Fix Subscriber model when removed within emit callback ([d0ed918](https://github.com/ethers-io/ethers.js/commit/d0ed91840c9f51c7ce9061ebb1d36727dbdd51a4)).
  - Fixed human-readable parser when identifier begins with valid type prefix ([#3728](https://github.com/ethers-io/ethers.js/issues/3728); [522fd16](https://github.com/ethers-io/ethers.js/commit/522fd16f68aabc53e4dc8745d4128e0d61260ed5)).
  - Update to latest secp256k1 library ([#3719](https://github.com/ethers-io/ethers.js/issues/3719); [803e8f9](https://github.com/ethers-io/ethers.js/commit/803e8f9821950b83efa876d64b1cfb35f6bccc38)).

ethers/v6.0.0 (2023-02-02 22:48)
--------------------------------

  - Initial release ([90afd9b](https://github.com/ethers-io/ethers.js/commit/90afd9bd81ed1408421a0247fa0845a74c9eb319)).
