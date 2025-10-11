/**
 *  @_subsection: api/wallet:JSON Wallets  [json-wallets]
 */
/**
 *  The data stored within a JSON Crowdsale wallet is fairly
 *  minimal.
 */
export type CrowdsaleAccount = {
    privateKey: string;
    address: string;
};
/**
 *  Returns true if %%json%% is a valid JSON Crowdsale wallet.
 */
export declare function isCrowdsaleJson(json: string): boolean;
/**
 *  Before Ethereum launched, it was necessary to create a wallet
 *  format for backers to use, which would be used to receive ether
 *  as a reward for contributing to the project.
 *
 *  The [[link-crowdsale]] format is now obsolete, but it is still
 *  useful to support and the additional code is fairly trivial as
 *  all the primitives required are used through core portions of
 *  the library.
 */
export declare function decryptCrowdsaleJson(json: string, _password: string | Uint8Array): CrowdsaleAccount;
//# sourceMappingURL=json-crowdsale.d.ts.map