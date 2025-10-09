# [3.14.0](https://github.com/cenk1cenk2/listr2/compare/v3.13.6...v3.14.0) (2022-01-04)

### Bug Fixes

- add tests and inject context variable as mutable ([afe3528](https://github.com/cenk1cenk2/listr2/commit/afe35289980a4bc89d8e021a997a3c6b011b58b6))

### Features

- ability to change the context type on subtasks ([7dccdfc](https://github.com/cenk1cenk2/listr2/commit/7dccdfc9563b3de2e059c43e0130f7777a3a2090)), closes [#612](https://github.com/cenk1cenk2/listr2/issues/612)

## [3.13.6](https://github.com/cenk1cenk2/listr2/compare/v3.13.5...v3.13.6) (2022-01-03)

### Bug Fixes

- update dependencies ([9ce590c](https://github.com/cenk1cenk2/listr2/commit/9ce590ca03e7954797e559a6999ed4ea9c6d27dd))

## [3.13.5](https://github.com/cenk1cenk2/listr2/compare/v3.13.4...v3.13.5) (2021-11-22)

### Bug Fixes

- swap clone package for rfdc to improve speed of error reporting ([a75c857](https://github.com/cenk1cenk2/listr2/commit/a75c8571e069f3aaca9538187027c9d72450635d))

## [3.13.4](https://github.com/cenk1cenk2/listr2/compare/v3.13.3...v3.13.4) (2021-11-17)

### Bug Fixes

- mark enquirer as optional as peer ([742395e](https://github.com/cenk1cenk2/listr2/commit/742395ec2d1674a1eae11e943bea1a0cd6733f16)), closes [#589](https://github.com/cenk1cenk2/listr2/issues/589)

## [3.13.3](https://github.com/cenk1cenk2/listr2/compare/v3.13.2...v3.13.3) (2021-11-02)

### Bug Fixes

- upgrade to rxjs7 ([f5fab40](https://github.com/cenk1cenk2/listr2/commit/f5fab401bb7e50023022abd7a0a77b6a02196ae7)), closes [#493](https://github.com/cenk1cenk2/listr2/issues/493) [#409](https://github.com/cenk1cenk2/listr2/issues/409)

## [3.13.2](https://github.com/cenk1cenk2/listr2/compare/v3.13.1...v3.13.2) (2021-11-02)

### Bug Fixes

- cloneing objects ([15e8317](https://github.com/cenk1cenk2/listr2/commit/15e8317cb3854e74a8c6d5f86983909cf34f89d8)), closes [#571](https://github.com/cenk1cenk2/listr2/issues/571) [#569](https://github.com/cenk1cenk2/listr2/issues/569) [#538](https://github.com/cenk1cenk2/listr2/issues/538)

## [3.13.1](https://github.com/cenk1cenk2/listr2/compare/v3.13.0...v3.13.1) (2021-10-23)

### Bug Fixes

- use v8 functions for error collection ([be37833](https://github.com/cenk1cenk2/listr2/commit/be37833807b2f915c53e58946543d257c723ac4b))

# [3.13.0](https://github.com/cenk1cenk2/listr2/compare/v3.12.2...v3.13.0) (2021-10-23)

### Bug Fixes

- ditch api-extractor update colorrette ([7ae6752](https://github.com/cenk1cenk2/listr2/commit/7ae6752d7da59e54c28caeb7b3297f1792b0c7c8))
- pass options to custom logger ([3004640](https://github.com/cenk1cenk2/listr2/commit/30046409eddba749b460d34cd9ef089bfcf300a4))

### Features

- pass options to the custom logger, implement it with types ([4cecba8](https://github.com/cenk1cenk2/listr2/commit/4cecba8a0b1f3efae5d89d982c67edcc82969218))

## [3.12.2](https://github.com/cenk1cenk2/listr2/compare/v3.12.1...v3.12.2) (2021-09-23)

### Bug Fixes

- commit message for pull request [#527](https://github.com/cenk1cenk2/listr2/issues/527) ([2b96129](https://github.com/cenk1cenk2/listr2/commit/2b96129dd38dd47cea77f757b0c9f2760001c0f4))

## [3.12.1](https://github.com/cenk1cenk2/listr2/compare/v3.12.0...v3.12.1) (2021-09-13)

### Bug Fixes

- **deps:** update dependency colorette to ^1.4.0 ([4f52e16](https://github.com/cenk1cenk2/listr2/commit/4f52e16f6251490ba4e8f4a3dc49b41a9a997048))

# [3.12.0](https://github.com/cenk1cenk2/listr2/compare/v3.11.1...v3.12.0) (2021-09-12)

### Features

- fix error collection and improve it a bit ([29a08bb](https://github.com/cenk1cenk2/listr2/commit/29a08bb53f3de4260e0ba60d94c375d0f9592058)), closes [#459](https://github.com/cenk1cenk2/listr2/issues/459)

## [3.11.1](https://github.com/cenk1cenk2/listr2/compare/v3.11.0...v3.11.1) (2021-08-31)

### Bug Fixes

- git hook ([5e5c111](https://github.com/cenk1cenk2/listr2/commit/5e5c111255a6bfb5f19bde0dae331ef7e883ba10))
- node 16 try/catch type changes ([a5e29f4](https://github.com/cenk1cenk2/listr2/commit/a5e29f412f8412002546657275030927146dae25))

# [3.11.0](https://github.com/cenk1cenk2/listr2/compare/v3.10.1...v3.11.0) (2021-07-22)

### Bug Fixes

- fix the tests and errors with the simple renderer ([ae4319b](https://github.com/cenk1cenk2/listr2/commit/ae4319be1797f029165c3fd2772abc5aae1e6b46))
- tiny bug with sending output through channel ([cce9eee](https://github.com/cenk1cenk2/listr2/commit/cce9eeeec4d3c8370b22d6da72d61fe25c13b6c5)), closes [#437](https://github.com/cenk1cenk2/listr2/issues/437)

### Features

- **renderer:** adds simple renderer which is neither updating nor verbose ([04a6858](https://github.com/cenk1cenk2/listr2/commit/04a6858fa8ce8c0b30bc24d81d9cef99ab5d6381))

## [3.10.1](https://github.com/cenk1cenk2/listr2/compare/v3.10.0...v3.10.1) (2021-07-22)

### Bug Fixes

- update deps ([84f3529](https://github.com/cenk1cenk2/listr2/commit/84f3529270637d04341aacbc5039ed8b52237b2e))

# [3.10.0](https://github.com/cenk1cenk2/listr2/compare/v3.9.0...v3.10.0) (2021-06-07)

### Features

- add context to the class itself for outside access ([98ea144](https://github.com/cenk1cenk2/listr2/commit/98ea14453257f9aec93932890e4c8c8d8ac53ead))

# [3.9.0](https://github.com/cenk1cenk2/listr2/compare/v3.8.6...v3.9.0) (2021-05-27)

### Features

- dependency cleaning merge ([07cc724](https://github.com/cenk1cenk2/listr2/commit/07cc72434db8c1ec743a9556890a572be9cd474d))
- export figures ([f7377d2](https://github.com/cenk1cenk2/listr2/commit/f7377d2fa771bc3ef05b4aa496f0a1c0a1ca8eec))

## [3.8.6](https://github.com/cenk1cenk2/listr2/compare/v3.8.5...v3.8.6) (2021-05-27)

### Bug Fixes

- add the missing test case ([b630e57](https://github.com/cenk1cenk2/listr2/commit/b630e5702b7d17dd802e7fb6a3d08d6d649e564a)), closes [#411](https://github.com/cenk1cenk2/listr2/issues/411)
- allow async skip boolean or string ([2289f3a](https://github.com/cenk1cenk2/listr2/commit/2289f3ab8b53a54adfdf76f2b64b802018c596fc))

## [3.8.5](https://github.com/cenk1cenk2/listr2/compare/v3.8.4...v3.8.5) (2021-05-27)

### Bug Fixes

- issue with enabling tasks ([0aa255e](https://github.com/cenk1cenk2/listr2/commit/0aa255ecc4638146d20ab897873d23ad92d960cb)), closes [#414](https://github.com/cenk1cenk2/listr2/issues/414)

## [3.8.4](https://github.com/cenk1cenk2/listr2/compare/v3.8.3...v3.8.4) (2021-05-25)

### Bug Fixes

- rollback rxjs ([36a02e1](https://github.com/cenk1cenk2/listr2/commit/36a02e1ec56d9a65e41d2adc34b3eabe0660bb38)), closes [#409](https://github.com/cenk1cenk2/listr2/issues/409)

## [3.8.3](https://github.com/cenk1cenk2/listr2/compare/v3.8.2...v3.8.3) (2021-05-24)

### Performance Improvements

- **deps:** replace `chalk` with `colorette` ([3014a16](https://github.com/cenk1cenk2/listr2/commit/3014a16420938a9c98a315a1233da630433460d8))

## [3.8.2](https://github.com/cenk1cenk2/listr2/compare/v3.8.1...v3.8.2) (2021-05-03)

### Bug Fixes

- update icons for windows ([6449de6](https://github.com/cenk1cenk2/listr2/commit/6449de6b3c4a5d369d8bbe5d0fd8571865783be2))

## [3.8.1](https://github.com/cenk1cenk2/listr2/compare/v3.8.0...v3.8.1) (2021-04-26)

### Bug Fixes

- **deps:** update dependency chalk to ^4.1.1 ([ef4bb19](https://github.com/cenk1cenk2/listr2/commit/ef4bb19dbbc82bb588abb2052f8771818f287aba))

# [3.8.0](https://github.com/cenk1cenk2/listr2/compare/v3.7.1...v3.8.0) (2021-04-25)

### Features

- use elegant spinner on environments that support unicode ([f71db87](https://github.com/cenk1cenk2/listr2/commit/f71db877060e1479b79f27b06dc3b7a84da51529))

## [3.7.1](https://github.com/cenk1cenk2/listr2/compare/v3.7.0...v3.7.1) (2021-04-19)

### Bug Fixes

- add auto generated docs for documentation site imports ([ae3786e](https://github.com/cenk1cenk2/listr2/commit/ae3786e4e4fbf8564a37dfc0c33bb0f5d9b1cc38))

# [3.7.0](https://github.com/cenk1cenk2/listr2/compare/v3.6.3...v3.7.0) (2021-04-18)

### Features

- adds task level exit on error ([9d27c2b](https://github.com/cenk1cenk2/listr2/commit/9d27c2b92eca3e0be60da3dcc858711c7ad52392))

## [3.6.3](https://github.com/cenk1cenk2/listr2/compare/v3.6.2...v3.6.3) (2021-04-17)

### Bug Fixes

- force commit for publish ([79ede29](https://github.com/cenk1cenk2/listr2/commit/79ede29516c16c516295af25f71a6a95e48a7d9e))

## [3.6.2](https://github.com/cenk1cenk2/listr2/compare/v3.6.1...v3.6.2) (2021-04-05)

### Bug Fixes

- just export the types ([0e787e9](https://github.com/cenk1cenk2/listr2/commit/0e787e9f3c3f62b9f16dd519be1fb0f3fa500ce9))

## [3.6.1](https://github.com/cenk1cenk2/listr2/compare/v3.6.0...v3.6.1) (2021-04-05)

### Bug Fixes

- fix exporting types in the old format ([f415027](https://github.com/cenk1cenk2/listr2/commit/f41502748d2e85b489a558dd35dd845648c34092))

# [3.6.0](https://github.com/cenk1cenk2/listr2/compare/v3.5.0...v3.6.0) (2021-04-05)

### Bug Fixes

- add missing imports ([91a5b5a](https://github.com/cenk1cenk2/listr2/commit/91a5b5aeb5b770646fda50db7ebb94326bc93a26))
- update some little things ([6eadb3a](https://github.com/cenk1cenk2/listr2/commit/6eadb3a82d402a04d5b163b318eca171175c7a04))

### Features

- fix types and styling ([ef8c9f9](https://github.com/cenk1cenk2/listr2/commit/ef8c9f99fbcc6f37c1c0810a420fbc39a357baa5))

# [3.5.0](https://github.com/cenk1cenk2/listr2/compare/v3.4.5...v3.5.0) (2021-04-05)

### Features

- adds timer in verbose renderer ([19e8b14](https://github.com/cenk1cenk2/listr2/commit/19e8b14f275c0d754de1a37f1d1e0495fda68a31)), closes [#320](https://github.com/cenk1cenk2/listr2/issues/320)

## [3.4.5](https://github.com/cenk1cenk2/listr2/compare/v3.4.4...v3.4.5) (2021-04-04)

### Bug Fixes

- fix issue with numeral prompt add example ([49e67a6](https://github.com/cenk1cenk2/listr2/commit/49e67a6c4385774790a1d83fb35bc4fdb4ea6d73)), closes [#325](https://github.com/cenk1cenk2/listr2/issues/325)

## [3.4.4](https://github.com/cenk1cenk2/listr2/compare/v3.4.3...v3.4.4) (2021-03-31)

### Bug Fixes

- **deps:** update dependency rxjs to ^6.6.7 ([1b00a87](https://github.com/cenk1cenk2/listr2/commit/1b00a877cbaaecafb3ec31457468a2553c8e777e))

## [3.4.3](https://github.com/cenk1cenk2/listr2/compare/v3.4.2...v3.4.3) (2021-03-08)

### Bug Fixes

- add enquirer import type for no type erors ([9a3f105](https://github.com/cenk1cenk2/listr2/commit/9a3f1059684511cdc4e100ac7059b5861b99e0c4))

## [3.4.2](https://github.com/cenk1cenk2/listr2/compare/v3.4.1...v3.4.2) (2021-03-08)

### Bug Fixes

- fix breaking the for ([456b681](https://github.com/cenk1cenk2/listr2/commit/456b681216e89d917a3b8f7c127a6563772bb2ae))

## [3.4.1](https://github.com/cenk1cenk2/listr2/compare/v3.4.0...v3.4.1) (2021-03-05)

### Bug Fixes

- return the last error as well from isRetrying ([f94641e](https://github.com/cenk1cenk2/listr2/commit/f94641e064464dddbf736e7f1dea1602a65ec433))

# [3.4.0](https://github.com/cenk1cenk2/listr2/compare/v3.3.4...v3.4.0) (2021-03-05)

### Features

- add retry feature ([4569fd2](https://github.com/cenk1cenk2/listr2/commit/4569fd262bb688198b44c58c6687d8d383664da5))

## [3.3.4](https://github.com/cenk1cenk2/listr2/compare/v3.3.3...v3.3.4) (2021-02-27)

### Bug Fixes

- **deps:** update dependency rxjs to ^6.6.6 ([0164fac](https://github.com/cenk1cenk2/listr2/commit/0164fac5afa0837496b6fb2c76a42e1f61f0111c))

## [3.3.3](https://github.com/cenk1cenk2/listr2/compare/v3.3.2...v3.3.3) (2021-02-23)

### Bug Fixes

- update how the renderer options are handled enabling to use task options ([2b147b2](https://github.com/cenk1cenk2/listr2/commit/2b147b24772a3133b9f8c456d5c302e0dba4b5ef))

## [3.3.2](https://github.com/cenk1cenk2/listr2/compare/v3.3.1...v3.3.2) (2021-02-21)

### Bug Fixes

- move documentation to site ([462ad71](https://github.com/cenk1cenk2/listr2/commit/462ad715782ef77fa3f991a8360392e261c05c03))

## [3.3.1](https://github.com/cenk1cenk2/listr2/compare/v3.3.0...v3.3.1) (2021-01-31)

### Bug Fixes

- rollback types ([7935241](https://github.com/cenk1cenk2/listr2/commit/7935241ef91ed36434242ee00ed838c1fe0979e2)), closes [#276](https://github.com/cenk1cenk2/listr2/issues/276)
- try fix typings issue ([4dd9013](https://github.com/cenk1cenk2/listr2/commit/4dd901356dffa24d3a3d41cf829896da7890e17e))
- update interface ([2cb2cd6](https://github.com/cenk1cenk2/listr2/commit/2cb2cd637efdbdadfff548ed0c9cccbb347ca5f6))

## [3.3.1-beta.3](https://github.com/cenk1cenk2/listr2/compare/v3.3.1-beta.2...v3.3.1-beta.3) (2021-01-31)

### Bug Fixes

- try fix typings issue ([4dd9013](https://github.com/cenk1cenk2/listr2/commit/4dd901356dffa24d3a3d41cf829896da7890e17e))

## [3.3.1-beta.2](https://github.com/cenk1cenk2/listr2/compare/v3.3.1-beta.1...v3.3.1-beta.2) (2021-01-25)

### Bug Fixes

- update interface ([2cb2cd6](https://github.com/cenk1cenk2/listr2/commit/2cb2cd637efdbdadfff548ed0c9cccbb347ca5f6))

## [3.3.1-beta.1](https://github.com/cenk1cenk2/listr2/compare/v3.3.0...v3.3.1-beta.1) (2021-01-24)

### Bug Fixes

- rollback types ([7935241](https://github.com/cenk1cenk2/listr2/commit/7935241ef91ed36434242ee00ed838c1fe0979e2)), closes [#276](https://github.com/cenk1cenk2/listr2/issues/276)

# [3.3.0](https://github.com/cenk1cenk2/listr2/compare/v3.2.3...v3.3.0) (2021-01-20)

### Bug Fixes

- add more filtering for empty lines ([8bc1671](https://github.com/cenk1cenk2/listr2/commit/8bc1671d58aba6d067ce03fd4882352a9a402bb4))
- drone stupidity ([3baa018](https://github.com/cenk1cenk2/listr2/commit/3baa018b5984d1c13aa4ebeb2cabba2764fa4ba2))
- fix drone ([af43b84](https://github.com/cenk1cenk2/listr2/commit/af43b840a7c8446b22d7e1dcb4dc527dfcac89d9))
- force build ([bc6cb28](https://github.com/cenk1cenk2/listr2/commit/bc6cb285f2cf17da5b12067279a87d6275397b98))
- some fixes for truncation and word wrapping ([18c279a](https://github.com/cenk1cenk2/listr2/commit/18c279a6a5a5b1273e7d372c16f264acf8593a4e))
- update readme, remove word-wrap ([2d6c6e8](https://github.com/cenk1cenk2/listr2/commit/2d6c6e8824ad93e3cd419e5aaaf3a5796d075484))
- update truncating and word wrap column thingies ([f8662b9](https://github.com/cenk1cenk2/listr2/commit/f8662b9c03d6138409945ce946389235b8e1bafb))

### Features

- added rollback stuff ([d80c060](https://github.com/cenk1cenk2/listr2/commit/d80c06052a1fdad3dcefda68ef3446d659ba191b))

# [3.3.0-beta.2](https://github.com/cenk1cenk2/listr2/compare/v3.3.0-beta.1...v3.3.0-beta.2) (2021-01-18)

### Bug Fixes

- add more filtering for empty lines ([8bc1671](https://github.com/cenk1cenk2/listr2/commit/8bc1671d58aba6d067ce03fd4882352a9a402bb4))
- some fixes for truncation and word wrapping ([18c279a](https://github.com/cenk1cenk2/listr2/commit/18c279a6a5a5b1273e7d372c16f264acf8593a4e))
- update truncating and word wrap column thingies ([f8662b9](https://github.com/cenk1cenk2/listr2/commit/f8662b9c03d6138409945ce946389235b8e1bafb))

# [3.3.0-beta.1](https://github.com/cenk1cenk2/listr2/compare/v3.2.3...v3.3.0-beta.1) (2021-01-17)

### Bug Fixes

- drone stupidity ([3baa018](https://github.com/cenk1cenk2/listr2/commit/3baa018b5984d1c13aa4ebeb2cabba2764fa4ba2))
- fix drone ([af43b84](https://github.com/cenk1cenk2/listr2/commit/af43b840a7c8446b22d7e1dcb4dc527dfcac89d9))
- force build ([bc6cb28](https://github.com/cenk1cenk2/listr2/commit/bc6cb285f2cf17da5b12067279a87d6275397b98))

### Features

- added rollback stuff ([d80c060](https://github.com/cenk1cenk2/listr2/commit/d80c06052a1fdad3dcefda68ef3446d659ba191b))

## [3.2.3](https://github.com/cenk1cenk2/listr2/compare/v3.2.2...v3.2.3) (2020-11-26)

### Bug Fixes

- update deps and fix typescript resolve ([836b8fd](https://github.com/cenk1cenk2/listr2/commit/836b8fde33a0d4bb8b2995ef3bad72dbf25a2a75))

## [3.2.2](https://github.com/cenk1cenk2/listr2/compare/v3.2.1...v3.2.2) (2020-10-26)

### Bug Fixes

- **prompt:** update task wrapper as this requirement for external use ([f0c0146](https://github.com/cenk1cenk2/listr2/commit/f0c01466d033a70560dd046362623b2fc4022da9))

## [3.2.1](https://github.com/cenk1cenk2/listr2/compare/v3.2.0...v3.2.1) (2020-10-24)

### Bug Fixes

- improve tests and disable the unnecassary cases ([929a616](https://github.com/cenk1cenk2/listr2/commit/929a6164444d7790f1a4bdd058378fc50b76e28d))

# [3.2.0](https://github.com/cenk1cenk2/listr2/compare/v3.1.1...v3.2.0) (2020-10-24)

### Bug Fixes

- fixed a tiny bug with newlistr ([51e4071](https://github.com/cenk1cenk2/listr2/commit/51e4071dd11c09d5cec4c0fafbf3368a7b165af7))

### Features

- Implemented some jsdoc style docs ([788fb99](https://github.com/cenk1cenk2/listr2/commit/788fb995da5a82a56d47d473dd3ed98a8c7cc457)), closes [#172](https://github.com/cenk1cenk2/listr2/issues/172)

## [3.1.1](https://github.com/cenk1cenk2/listr2/compare/v3.1.0...v3.1.1) (2020-09-22)

### Bug Fixes

- **prompt:** make prompt outside used ([2a61ac8](https://github.com/cenk1cenk2/listr2/commit/2a61ac80c5121ee020abc5b268c540eefad3738d))
- **prompt:** reenabled external use ([2408aa1](https://github.com/cenk1cenk2/listr2/commit/2408aa1391fb65f07cbcade698a0e834d38b2231))

# [3.1.0](https://github.com/cenk1cenk2/listr2/compare/v3.0.1...v3.1.0) (2020-09-20)

### Bug Fixes

- **prompt:** prompt.submit instead of prompt.cancel to not throw error ([b758dac](https://github.com/cenk1cenk2/listr2/commit/b758dace3ddc3ff731b2689c7b4fd1a467ff90f9))
- trying for adding skip functionality to prompt ([71924c9](https://github.com/cenk1cenk2/listr2/commit/71924c97b4a79077934530c02a6dcd3ecd968741)), closes [#173](https://github.com/cenk1cenk2/listr2/issues/173)
- trying for fix ([79ba2bb](https://github.com/cenk1cenk2/listr2/commit/79ba2bb2005a3d646c9e5fafc1347fdc4a369cc7))
- **deps:** update dependency rxjs to ^6.6.3 ([6664562](https://github.com/cenk1cenk2/listr2/commit/6664562749eb422436166f73668de12c0d0297ec))

### Features

- code style for cancel prompt ([4737669](https://github.com/cenk1cenk2/listr2/commit/4737669ec2ce75d46afef3402760fb959f1b7424)), closes [#173](https://github.com/cenk1cenk2/listr2/issues/173)

## [3.0.1](https://github.com/cenk1cenk2/listr2/compare/v3.0.0...v3.0.1) (2020-09-05)

### Bug Fixes

- **default-renderer:** added some fixes to swallowing error output in collapseErrors: [secure] mode and showErrorMessage ([b0c2bb7](https://github.com/cenk1cenk2/listr2/commit/b0c2bb7d11cd3b3e9cdffdaa4a6a2dfab725a0c7))

# [3.0.0](https://github.com/cenk1cenk2/listr2/compare/v2.6.2...v3.0.0) (2020-09-04)

### Bug Fixes

- fix subtasks rendering ([c11aea0](https://github.com/cenk1cenk2/listr2/commit/c11aea05e4ca749e4c92cdd69d358765a43451c4))
- lost message ([c5cc510](https://github.com/cenk1cenk2/listr2/commit/c5cc51028c2d9dccd28ea1f635288f4e5ba38f0d)), closes [#163](https://github.com/cenk1cenk2/listr2/issues/163) [#163](https://github.com/cenk1cenk2/listr2/issues/163)

### Features

- **default-renderer:** added collapse errors changed the renderer a bit ([514fc87](https://github.com/cenk1cenk2/listr2/commit/514fc87bb2595cc1a09cb865d60a380b0f71a9ec)), closes [#163](https://github.com/cenk1cenk2/listr2/issues/163)

### Performance Improvements

- changed last rendering method ([bd38146](https://github.com/cenk1cenk2/listr2/commit/bd38146c692127abb09cd754f2be0aac306efda4))

### BREAKING CHANGES

- Tests might break with this release, if they directly rely on default-renderer. Especially the snapshot testing will get hit.

* default-renderer now utilizes different EOL depending on the platform.
* The last rendering method has been changed therefore it will leave a empty line before doing the last render which is the log-update clean functionallity, before writing it with process.stdout.
* Outputted data now gets better trimmed which might cause testing to not match.
* More consistent spacing is introduced for rendering the subtasks, bottom bar and the prompt bar.

* error-collection was not working as expected but it might now cause some tests to fail.

Overall there are no breaking changes introduced to the code directly but it might cause the tests which rely on default-renderer, since the rendering method is almost completely revised.

# [3.0.0-beta.1](https://github.com/cenk1cenk2/listr2/compare/v2.6.2...v3.0.0-beta.1) (2020-09-04)

### Bug Fixes

- fix subtasks rendering ([c11aea0](https://github.com/cenk1cenk2/listr2/commit/c11aea05e4ca749e4c92cdd69d358765a43451c4))
- lost message ([c5cc510](https://github.com/cenk1cenk2/listr2/commit/c5cc51028c2d9dccd28ea1f635288f4e5ba38f0d)), closes [#163](https://github.com/cenk1cenk2/listr2/issues/163) [#163](https://github.com/cenk1cenk2/listr2/issues/163)

### Features

- **default-renderer:** added collapse errors changed the renderer a bit ([514fc87](https://github.com/cenk1cenk2/listr2/commit/514fc87bb2595cc1a09cb865d60a380b0f71a9ec)), closes [#163](https://github.com/cenk1cenk2/listr2/issues/163)

### Performance Improvements

- changed last rendering method ([bd38146](https://github.com/cenk1cenk2/listr2/commit/bd38146c692127abb09cd754f2be0aac306efda4))

### BREAKING CHANGES

- Tests might break with this release, if they directly rely on default-renderer. Especially the snapshot testing will get hit.

* default-renderer now utilizes different EOL depending on the platform.
* The last rendering method has been changed therefore it will leave a empty line before doing the last render which is the log-update clean functionallity, before writing it with process.stdout.
* Outputted data now gets better trimmed which might cause testing to not match.
* More consistent spacing is introduced for rendering the subtasks, bottom bar and the prompt bar.

* error-collection was not working as expected but it might now cause some tests to fail.

Overall there are no breaking changes introduced to the code directly but it might cause the tests which rely on default-renderer, since the rendering method is almost completely revised.

## [2.6.2](https://github.com/cenk1cenk2/listr2/compare/v2.6.1...v2.6.2) (2020-08-29)

### Bug Fixes

- **default-renderer:** timer with title change ([6cf1eec](https://github.com/cenk1cenk2/listr2/commit/6cf1eec57346246120cb5e75282da9e10ebe3748))

## [2.6.1](https://github.com/cenk1cenk2/listr2/compare/v2.6.0...v2.6.1) (2020-08-27)

### Bug Fixes

- new version for replicate.npmjs ([09dcb9c](https://github.com/cenk1cenk2/listr2/commit/09dcb9cbcafb7222222560c84cd8e0a08916ef1b))

# [2.6.0](https://github.com/cenk1cenk2/listr2/compare/v2.5.1...v2.6.0) (2020-08-16)

### Bug Fixes

- keep persistent output on error ([de7e661](https://github.com/cenk1cenk2/listr2/commit/de7e661c15f9fba020e66cd098426f47cf08c1db))

### Features

- **listr:** accessing parent task ([544a130](https://github.com/cenk1cenk2/listr2/commit/544a1304ff5e642621ae1ed14358947b04cb3f91)), closes [#141](https://github.com/cenk1cenk2/listr2/issues/141)
- isolated error and skip messages ([5b8735d](https://github.com/cenk1cenk2/listr2/commit/5b8735d53ba7325e0d3a5aa1ec5989b1cc353610))
- **default-renderer:** added timer to renderer ([4b8d757](https://github.com/cenk1cenk2/listr2/commit/4b8d757648153305090d00c3f885fec3ac5a0fe0))

## [2.5.1](https://github.com/cenk1cenk2/listr2/compare/v2.5.0...v2.5.1) (2020-08-10)

### Bug Fixes

- **prompt:** fixed an issue with one prompt not returning default ([375a441](https://github.com/cenk1cenk2/listr2/commit/375a441cfc560b550c639fe4b977ee2d74aad755))

# [2.5.0](https://github.com/cenk1cenk2/listr2/compare/v2.4.1...v2.5.0) (2020-08-10)

### Bug Fixes

- **deps:** update dependency rxjs to ^6.6.2 ([5175991](https://github.com/cenk1cenk2/listr2/commit/5175991e471a2c4a3f6621026657744ae59c9b43))
- **prompt:** enquirer custom prompts ([6317ec6](https://github.com/cenk1cenk2/listr2/commit/6317ec6d4aac2f3467dd6dc37a98f05baeb244b6))

### Features

- **renderer:** added disable color and enable silent renderer via options ([74f91c2](https://github.com/cenk1cenk2/listr2/commit/74f91c2269316b2bac22bb450c14972e0dd56dde))

## [2.4.1](https://github.com/cenk1cenk2/listr2/compare/v2.4.0...v2.4.1) (2020-07-29)

### Bug Fixes

- **default-renderer:** added a tiny fix when persistent bottom bar is enabled and task is skipped ([d6a25a8](https://github.com/cenk1cenk2/listr2/commit/d6a25a886224bf6d0ac3c3a7253901f1fb74dc59))

# [2.4.0](https://github.com/cenk1cenk2/listr2/compare/v2.3.6...v2.4.0) (2020-07-27)

### Bug Fixes

- **deps:** removed bundle of rxjs ([a103acb](https://github.com/cenk1cenk2/listr2/commit/a103acb040cd8b89c67dea17b5aa9e63730af269))
- **rxjs:** retry for rxjs export with webpack ([ac537e5](https://github.com/cenk1cenk2/listr2/commit/ac537e5beb2c096acdbb6cb2725f9d7aa434a26d))

### Features

- **build:** bundle rxjs with webpack, reduce total bundle size, since i started to use this everywhere ([4cc922a](https://github.com/cenk1cenk2/listr2/commit/4cc922a94a21899973aeca371e4078fa9205e053))

### Reverts

- **deps:** rxjs bundle ([4067164](https://github.com/cenk1cenk2/listr2/commit/4067164ed993368997986223bbec3c22059f27b8))

# [2.4.0-beta.3](https://github.com/cenk1cenk2/listr2/compare/v2.4.0-beta.2...v2.4.0-beta.3) (2020-07-27)

### Bug Fixes

- **deps:** removed bundle of rxjs ([a103acb](https://github.com/cenk1cenk2/listr2/commit/a103acb040cd8b89c67dea17b5aa9e63730af269))

### Reverts

- **deps:** rxjs bundle ([4067164](https://github.com/cenk1cenk2/listr2/commit/4067164ed993368997986223bbec3c22059f27b8))

# [2.4.0-beta.2](https://github.com/cenk1cenk2/listr2/compare/v2.4.0-beta.1...v2.4.0-beta.2) (2020-07-27)

### Bug Fixes

- **rxjs:** retry for rxjs export with webpack ([ac537e5](https://github.com/cenk1cenk2/listr2/commit/ac537e5beb2c096acdbb6cb2725f9d7aa434a26d))

# [2.4.0-beta.1](https://github.com/cenk1cenk2/listr2/compare/v2.3.6...v2.4.0-beta.1) (2020-07-27)

### Features

- **build:** bundle rxjs with webpack, reduce total bundle size, since i started to use this everywhere ([4cc922a](https://github.com/cenk1cenk2/listr2/commit/4cc922a94a21899973aeca371e4078fa9205e053))

## [2.3.6](https://github.com/cenk1cenk2/listr2/compare/v2.3.5...v2.3.6) (2020-07-27)

### Bug Fixes

- remove unused import ([46a72c7](https://github.com/cenk1cenk2/listr2/commit/46a72c7d16d5ae882e4fa23e9064b3f0ad008792))
- **default-renderer:** fix output rendering with empty subtasks ([8299c3f](https://github.com/cenk1cenk2/listr2/commit/8299c3fe8324bdade582e1e0052a4463039f52e3))
- **default-renderer:** output from subtask of subtask ([4096e62](https://github.com/cenk1cenk2/listr2/commit/4096e62f058082f15cc494c6a406cd0bdef4e641))

## [2.3.5](https://github.com/cenk1cenk2/listr2/compare/v2.3.4...v2.3.5) (2020-07-26)

### Bug Fixes

- **default-renderer:** renderer to show spinner if all subtasks has no title ([58aaadc](https://github.com/cenk1cenk2/listr2/commit/58aaadc08924ea4657caa86850c5d9040fb9d1f5))
- **deps:** update all minor dependency updates ([4fccbc4](https://github.com/cenk1cenk2/listr2/commit/4fccbc4382c3b41e374070166a1ecb558ab77c66))

## [2.3.4](https://github.com/cenk1cenk2/listr2/compare/v2.3.3...v2.3.4) (2020-07-26)

### Bug Fixes

- **default-renderer:** fixed the issue when there is all empty subtasks and it leaves one extra space ([57b0809](https://github.com/cenk1cenk2/listr2/commit/57b08097bdd83bca40fbd89cd823fc1d175fa612))

## [2.3.3](https://github.com/cenk1cenk2/listr2/compare/v2.3.2...v2.3.3) (2020-07-24)

### Bug Fixes

- **prompts:** removed prompt bind type to use it in other scripts directly ([655334a](https://github.com/cenk1cenk2/listr2/commit/655334a256524cb8099c189868bb8f30dc784b90))

## [2.3.2](https://github.com/cenk1cenk2/listr2/compare/v2.3.1...v2.3.2) (2020-07-23)

### Bug Fixes

- **tests:** change env variable for tests, esspecially chalk because node_env test is more common ([5c7c9ca](https://github.com/cenk1cenk2/listr2/commit/5c7c9caf33eb5141d46cf79cd7176826807b9e50))

## [2.3.1](https://github.com/cenk1cenk2/listr2/compare/v2.3.0...v2.3.1) (2020-07-22)

### Bug Fixes

- **readme:** added badge for npm ([61f6bc3](https://github.com/cenk1cenk2/listr2/commit/61f6bc36a5df27b80d61233dd0880326b93b7d5a))

# [2.3.0](https://github.com/cenk1cenk2/listr2/compare/v2.2.1...v2.3.0) (2020-07-22)

### Bug Fixes

- **colors:** disable colors for test ([b81ee08](https://github.com/cenk1cenk2/listr2/commit/b81ee087fd11f9ee8b96b305d9a76fb7b245ca9c))
- **deps:** update all minor package updates ([aba8cf2](https://github.com/cenk1cenk2/listr2/commit/aba8cf20abbf6c81cd98be41099254ba6c30a19b))
- **truncate:** fix truncate to 80 on columns unknown ([3454aed](https://github.com/cenk1cenk2/listr2/commit/3454aedbc4282550f79f4e65fe34ab14fbe06e4e))

### Features

- added lazy option to default renderer. moved enquirer to inject wrapper key from root ([78f3984](https://github.com/cenk1cenk2/listr2/commit/78f3984c19cd31f45edf5fbc8e8bfa5380104331))
- **prompts:** added external enquirer injection for testing, fallback condition, fixed catching err ([a0bf6fd](https://github.com/cenk1cenk2/listr2/commit/a0bf6fd444caf69b0231f710099e367840c0ed15)), closes [#66](https://github.com/cenk1cenk2/listr2/issues/66) [#67](https://github.com/cenk1cenk2/listr2/issues/67) [#68](https://github.com/cenk1cenk2/listr2/issues/68)

# [2.3.0-beta.2](https://github.com/cenk1cenk2/listr2/compare/v2.3.0-beta.1...v2.3.0-beta.2) (2020-07-22)

### Features

- added lazy option to default renderer. moved enquirer to inject wrapper key from root ([78f3984](https://github.com/cenk1cenk2/listr2/commit/78f3984c19cd31f45edf5fbc8e8bfa5380104331))

# [2.3.0-beta.1](https://github.com/cenk1cenk2/listr2/compare/v2.2.1...v2.3.0-beta.1) (2020-07-22)

### Bug Fixes

- **deps:** update all minor package updates ([aba8cf2](https://github.com/cenk1cenk2/listr2/commit/aba8cf20abbf6c81cd98be41099254ba6c30a19b))

### Features

- **prompts:** added external enquirer injection for testing, fallback condition, fixed catching err ([a0bf6fd](https://github.com/cenk1cenk2/listr2/commit/a0bf6fd444caf69b0231f710099e367840c0ed15)), closes [#66](https://github.com/cenk1cenk2/listr2/issues/66) [#67](https://github.com/cenk1cenk2/listr2/issues/67) [#68](https://github.com/cenk1cenk2/listr2/issues/68)

## [2.2.1](https://github.com/cenk1cenk2/listr2/compare/v2.2.0...v2.2.1) (2020-07-18)

### Bug Fixes

- **prompts:** added return when prompt error ([6c89e56](https://github.com/cenk1cenk2/listr2/commit/6c89e562713686a1748a0436aef3c2ae43c6c555))
- **prompts:** fixed prompt error message when enquirer is not installed optionally ([8fc5849](https://github.com/cenk1cenk2/listr2/commit/8fc58492bcac3fb5520360c7c8d1e5c2156b74fc))

# [2.2.0](https://github.com/cenk1cenk2/listr2/compare/v2.1.9...v2.2.0) (2020-07-03)

### Features

- display elegant spinner on Windows Terminal ([a86868b](https://github.com/cenk1cenk2/listr2/commit/a86868b7638f5b63b64f70e7559ace07d598c84a))

## [2.1.9](https://github.com/cenk1cenk2/listr2/compare/v2.1.8...v2.1.9) (2020-07-01)

### Bug Fixes

- **manager:** manager type problem with indent ([9444d3d](https://github.com/cenk1cenk2/listr2/commit/9444d3dcc5c7d1d72aa424441cc0b150effedebd))

## [2.1.9-beta.1](https://github.com/cenk1cenk2/listr2/compare/v2.1.8...v2.1.9-beta.1) (2020-06-18)

### Bug Fixes

- **manager:** manager type problem with indent ([9444d3d](https://github.com/cenk1cenk2/listr2/commit/9444d3dcc5c7d1d72aa424441cc0b150effedebd))

## [2.1.8](https://github.com/cenk1cenk2/listr2/compare/v2.1.7...v2.1.8) (2020-06-17)

### Bug Fixes

- **renderer:** add skip to verbose output ([f577df0](https://github.com/cenk1cenk2/listr2/commit/f577df08720a6602a46b9eec457a9d55321d89d7))

## [2.1.7](https://github.com/cenk1cenk2/listr2/compare/v2.1.6...v2.1.7) (2020-06-14)

### Bug Fixes

- **renderer:** verbose renderer ([794f966](https://github.com/cenk1cenk2/listr2/commit/794f9667f8d2b1715f76a841dcb73f47bf8d6aca))

## [2.1.6](https://github.com/cenk1cenk2/listr2/compare/v2.1.5...v2.1.6) (2020-06-14)

### Bug Fixes

- **renderer:** add defaults ([8d3436d](https://github.com/cenk1cenk2/listr2/commit/8d3436d74dfe904f1259f85cfa251445f5c58e84))

## [2.1.5](https://github.com/cenk1cenk2/listr2/compare/v2.1.4...v2.1.5) (2020-06-14)

### Bug Fixes

- **renderer:** verbose renderer defaults ([3246fe1](https://github.com/cenk1cenk2/listr2/commit/3246fe1deb19dd2878d5c86ee2ca98d9a7b2f26a))

## [2.1.4](https://github.com/cenk1cenk2/listr2/compare/v2.1.3...v2.1.4) (2020-06-14)

### Bug Fixes

- **added verbose renderer options:** added new options of log empty title and title change ([5a5eb79](https://github.com/cenk1cenk2/listr2/commit/5a5eb79e5d9097b84fc74722de85c6f60e0f288e))
- **types:** enquirer types ([d309d91](https://github.com/cenk1cenk2/listr2/commit/d309d91241ec85f52d54b974f6391f7c640ea1ae))

## [2.1.3](https://github.com/cenk1cenk2/listr2/compare/v2.1.2...v2.1.3) (2020-06-04)

### Bug Fixes

- **enquirer:** moved prompt flattening around again for my own scripts ([a40a569](https://github.com/cenk1cenk2/listr2/commit/a40a569785dec64d14186fa997bf8bebcd219390))
- **enquirer:** optional stdout ([703658f](https://github.com/cenk1cenk2/listr2/commit/703658f3fe84f91e74173932c91b609380d40c59))

## [2.1.2](https://github.com/cenk1cenk2/listr2/compare/v2.1.1...v2.1.2) (2020-06-04)

### Bug Fixes

- **prompt:** added option to call prompt from outside for my applicatiosn ([27dbdfa](https://github.com/cenk1cenk2/listr2/commit/27dbdfa5068eed7570293468455515ed1c7860ba))

## [2.1.1](https://github.com/cenk1cenk2/listr2/compare/v2.1.0...v2.1.1) (2020-06-04)

### Bug Fixes

- **streams:** add legacy streams to accepted types ([f63dd52](https://github.com/cenk1cenk2/listr2/commit/f63dd52167c2babada80ff5d092843ead2ca86e7))

# [2.1.0](https://github.com/cenk1cenk2/listr2/compare/v2.0.4...v2.1.0) (2020-06-03)

### Bug Fixes

- **deps:** remove trivial deps ([de8dec0](https://github.com/cenk1cenk2/listr2/commit/de8dec09b45fa09ddc8afb1d7742846ba3b620dd))
- **deps:** remove unnecassary types ([b37f416](https://github.com/cenk1cenk2/listr2/commit/b37f416fbed04d531b1dca5495d7008ecedf4ab5))
- **deps:** updated deps to latest ([c4ad38f](https://github.com/cenk1cenk2/listr2/commit/c4ad38f32510d598a4c93d19ca517eef81c841a2))
- **figures:** made microsoft icons to use the fancy ones, even though it may fail in some cases ([f0e5817](https://github.com/cenk1cenk2/listr2/commit/f0e581706e59d9b96da9bd050a1ad3638b59c2aa)), closes [#31](https://github.com/cenk1cenk2/listr2/issues/31)
- **prompt:** enquirer to peer ([cae55e9](https://github.com/cenk1cenk2/listr2/commit/cae55e962faf54f3ddadc6c220567a316c8ee15b))
- **prompt:** types ([110130a](https://github.com/cenk1cenk2/listr2/commit/110130a6c0a6b3443362cd8fc018e18b6ef5fbbc))
- **prompts:** fixed type for array prompts, added name as mandatory ([a08b1e4](https://github.com/cenk1cenk2/listr2/commit/a08b1e4a9b80fd542384ef3a5dbc111dead0bd6c))
- **stream:** fixed streams added example ([614d89f](https://github.com/cenk1cenk2/listr2/commit/614d89fc1b64e7a586a7a590233d4dce1696b7b4)), closes [#37](https://github.com/cenk1cenk2/listr2/issues/37)

### Features

- **prompt:** make prompt module optional, be more compatible to underlying enqurier ([64cecc1](https://github.com/cenk1cenk2/listr2/commit/64cecc10049f5802a6e7a71071ec698e1226bdc2)), closes [#34](https://github.com/cenk1cenk2/listr2/issues/34)
- **prompt:** use enquirer directly ([b34e9d0](https://github.com/cenk1cenk2/listr2/commit/b34e9d0b2ef9b0cbf723759c5a236eca8ac86af0)), closes [#34](https://github.com/cenk1cenk2/listr2/issues/34)
- **renderer:** added hook and stdout support ([bd73c68](https://github.com/cenk1cenk2/listr2/commit/bd73c68b9eb21cd100a266ce05ba36af0c727a4f)), closes [#31](https://github.com/cenk1cenk2/listr2/issues/31)

# [2.1.0-beta.6](https://github.com/cenk1cenk2/listr2/compare/v2.1.0-beta.5...v2.1.0-beta.6) (2020-06-03)

### Bug Fixes

- **deps:** remove trivial deps ([de8dec0](https://github.com/cenk1cenk2/listr2/commit/de8dec09b45fa09ddc8afb1d7742846ba3b620dd))
- **deps:** remove unnecassary types ([b37f416](https://github.com/cenk1cenk2/listr2/commit/b37f416fbed04d531b1dca5495d7008ecedf4ab5))
- **deps:** updated deps to latest ([c4ad38f](https://github.com/cenk1cenk2/listr2/commit/c4ad38f32510d598a4c93d19ca517eef81c841a2))
- **stream:** fixed streams added example ([614d89f](https://github.com/cenk1cenk2/listr2/commit/614d89fc1b64e7a586a7a590233d4dce1696b7b4)), closes [#37](https://github.com/cenk1cenk2/listr2/issues/37)

# [2.1.0-beta.5](https://github.com/cenk1cenk2/listr2/compare/v2.1.0-beta.4...v2.1.0-beta.5) (2020-06-03)

### Bug Fixes

- **prompt:** types ([110130a](https://github.com/cenk1cenk2/listr2/commit/110130a6c0a6b3443362cd8fc018e18b6ef5fbbc))

# [2.1.0-beta.4](https://github.com/cenk1cenk2/listr2/compare/v2.1.0-beta.3...v2.1.0-beta.4) (2020-06-02)

### Bug Fixes

- **prompt:** enquirer to peer ([cae55e9](https://github.com/cenk1cenk2/listr2/commit/cae55e962faf54f3ddadc6c220567a316c8ee15b))

# [2.1.0-beta.3](https://github.com/cenk1cenk2/listr2/compare/v2.1.0-beta.2...v2.1.0-beta.3) (2020-06-02)

### Bug Fixes

- **prompts:** fixed type for array prompts, added name as mandatory ([a08b1e4](https://github.com/cenk1cenk2/listr2/commit/a08b1e4a9b80fd542384ef3a5dbc111dead0bd6c))

# [2.1.0-beta.2](https://github.com/cenk1cenk2/listr2/compare/v2.1.0-beta.1...v2.1.0-beta.2) (2020-06-02)

### Features

- **prompt:** make prompt module optional, be more compatible to underlying enqurier ([64cecc1](https://github.com/cenk1cenk2/listr2/commit/64cecc10049f5802a6e7a71071ec698e1226bdc2)), closes [#34](https://github.com/cenk1cenk2/listr2/issues/34)
- **prompt:** use enquirer directly ([b34e9d0](https://github.com/cenk1cenk2/listr2/commit/b34e9d0b2ef9b0cbf723759c5a236eca8ac86af0)), closes [#34](https://github.com/cenk1cenk2/listr2/issues/34)

# [2.1.0-beta.1](https://github.com/cenk1cenk2/listr2/compare/v2.0.4...v2.1.0-beta.1) (2020-05-25)

### Bug Fixes

- **figures:** made microsoft icons to use the fancy ones, even though it may fail in some cases ([f0e5817](https://github.com/cenk1cenk2/listr2/commit/f0e581706e59d9b96da9bd050a1ad3638b59c2aa)), closes [#31](https://github.com/cenk1cenk2/listr2/issues/31)

### Features

- **renderer:** added hook and stdout support ([bd73c68](https://github.com/cenk1cenk2/listr2/commit/bd73c68b9eb21cd100a266ce05ba36af0c727a4f)), closes [#31](https://github.com/cenk1cenk2/listr2/issues/31)

## [2.0.4](https://github.com/cenk1cenk2/listr2/compare/v2.0.3...v2.0.4) (2020-05-20)

### Bug Fixes

- **types:** match version of uuid ([33a1e80](https://github.com/cenk1cenk2/listr2/commit/33a1e8007a82015171ca55c86a71fbbc017d6e4d))
- **uuid:** added implicit tests for 13.6, rollback to uuid working version ([75ade63](https://github.com/cenk1cenk2/listr2/commit/75ade636b63606ee243e2591e60e8e72b5f1c1ca)), closes [#28](https://github.com/cenk1cenk2/listr2/issues/28)

## [2.0.3](https://github.com/cenk1cenk2/listr2/compare/v2.0.2...v2.0.3) (2020-05-19)

### Bug Fixes

- **deps:** exchange uuid with nanoid ([2048b3d](https://github.com/cenk1cenk2/listr2/commit/2048b3d953ab5cab0cf67ffe26fa24fb987e6b6e)), closes [#25](https://github.com/cenk1cenk2/listr2/issues/25)

## [2.0.2](https://github.com/cenk1cenk2/listr2/compare/v2.0.1...v2.0.2) (2020-05-18)

### Bug Fixes

- **deps:** rollback uuid to ^7 ([9ba257d](https://github.com/cenk1cenk2/listr2/commit/9ba257d9b19ce4534982baac358096fedb21f2b1)), closes [#25](https://github.com/cenk1cenk2/listr2/issues/25)

## [2.0.1](https://github.com/cenk1cenk2/listr2/compare/v2.0.0...v2.0.1) (2020-05-06)

### Bug Fixes

- **manager:** fixed manager types ([10d74e9](https://github.com/cenk1cenk2/listr2/commit/10d74e9f481fee689f103a08c42c3c60d0fb2bc1)), closes [#22](https://github.com/cenk1cenk2/listr2/issues/22)
- **manager:** fixed types for manager ([033c7d1](https://github.com/cenk1cenk2/listr2/commit/033c7d180431a7039c9c38a8537b43fc5615f50e))

# [2.0.0](https://github.com/cenk1cenk2/listr2/compare/v1.3.12...v2.0.0) (2020-05-06)

### Bug Fixes

- **default-renderer:** added back cli truncate ([22132a5](https://github.com/cenk1cenk2/listr2/commit/22132a5b022ef58a4a463e48af062f54631a3b9d))
- **error-collection:** fixed error collection on non-failing tasks ([4239094](https://github.com/cenk1cenk2/listr2/commit/4239094a7947cf60d8d030c45aaf75710637a40c))
- **manager:** added error context ([4f8f387](https://github.com/cenk1cenk2/listr2/commit/4f8f387a576bc83947fd90e83f27de827b9f9d08))
- **manager:** fixed manager ([57dcd7f](https://github.com/cenk1cenk2/listr2/commit/57dcd7f8362589f2a43b645920cf158c2cb8d591))
- **types:** fix ([b3ee9be](https://github.com/cenk1cenk2/listr2/commit/b3ee9be0f895e8927c825b3993cc847d360e709d))
- fixed types for isolated renderer options ([4521832](https://github.com/cenk1cenk2/listr2/commit/452183240c55984db57551082aa049e4799a2425))

### Features

- **release:** ready to update to new version ([50fb773](https://github.com/cenk1cenk2/listr2/commit/50fb773128073b1ec312fea3121a2f93e9270271)), closes [#19](https://github.com/cenk1cenk2/listr2/issues/19) [#18](https://github.com/cenk1cenk2/listr2/issues/18)
- **renderer-options:** started to isolate the renderer options instead of writing them directly ([95f7f87](https://github.com/cenk1cenk2/listr2/commit/95f7f8749445e45a90d3f4346eb4cd0625e9593e))

### BREAKING CHANGES

- **release:** - Renderer Options
  - Reason: _This was changed because of having all the renderer options that are mangled together and not respecting which renderer has been choosen. It also allows for custom renderers to have their own logic by exposing their options in a single class file rather than expecting that functionality from the project itself._
  - Before <v1.3.12:
  ```typescript
    new Listr<Ctx>([
    {
      task: async (ctx, task): Promise<void> => {
      },
      persistentOutput: true
    }
  ], {
    concurrent: [secure],
    collapse: true
  ```
  - After <v1.3.12:
  ```typescript
  new Listr<Ctx>(
    [
      {
        task: async (ctx, task): Promise<void> => {},
        options: { persistentOutput: true } // per task based options are moved to their own key
      }
    ],
    {
      concurrent: [secure],
      rendererOptions: { collapse: [secure] }
      // global renderer options moved to their own key
    }
  )
  ```

* Some of the types has been changed.

  - Reason: _Some of the types had to be changed due to compatability reasons with new autocomplete functionality of the dynamic renderer options._
  - Before <v1.3.12:

  ```typescript
  let task: Listr<Ctx>

  task = new Listr(..., { renderer: 'verbose' })
  ```

  - After <v1.3.12:

  ```typescript
  // this without the indication of verbose will now fail due to default renderer being 'default' for autocompleting goodness of the IDEs.
  // So you have to overwrite it manually to 'verbose'.
  // If it does not have a default you had to explicitly write { renderer: 'default' } everytime to have the auto complete feature
  let task: Listr<Ctx, 'verbose'>

  task = new Listr(..., { renderer: 'verbose' })
  ```

* Test renderer removed.
  - Reason: _On non-tty environments that the verbose renderer is intended for there is no need to show icons. Since icons are now optional with the default being disabled for the verbose renderer, there is no need for a renderer that does have the same functionality since verbose and test are now basically the same thing. Verbose seemed a better name then test, so I had to remove test from the equation._
  - Before <v1.3.12:
  ```typescript
  const task = new Listr(..., { renderer: 'test' })
  ```
  - After <v1.3.12:
  ```typescript
  const task = new Listr(..., { renderer: 'verbose' })
  ```

## [1.3.12](https://github.com/cenk1cenk2/listr2/compare/v1.3.11...v1.3.12) (2020-04-30)

### Bug Fixes

- **ignore:** note to self dont do late night commits ([56ff7b7](https://github.com/cenk1cenk2/listr2/commit/56ff7b79b010606c593348e6b27fcd455d1c2dcd))

## [1.3.11](https://github.com/cenk1cenk2/listr2/compare/v1.3.10...v1.3.11) (2020-04-30)

### Bug Fixes

- **build:** ignored tests files ([16d8d93](https://github.com/cenk1cenk2/listr2/commit/16d8d9336fabbfb311a821744707e8ae55e80334))

## [1.3.10](https://github.com/cenk1cenk2/listr2/compare/v1.3.9...v1.3.10) (2020-04-30)

### Bug Fixes

- **tests:** add tests to npm ignore ([83cd9d3](https://github.com/cenk1cenk2/listr2/commit/83cd9d3c1270dc8f48458d329b01ed638eff6340))

## [1.3.9](https://github.com/cenk1cenk2/listr2/compare/v1.3.8...v1.3.9) (2020-04-30)

### Bug Fixes

- added e2e and unit tests, not comprehensive ([4d3076b](https://github.com/cenk1cenk2/listr2/commit/4d3076b80c2adb7a22388178f3e31690dec37534))

### Reverts

- **task:** revert back to enable boolean for not breaking compatability ([45b6c32](https://github.com/cenk1cenk2/listr2/commit/45b6c32fe451e138bad36f95d4d9ade1b49f45a2))
