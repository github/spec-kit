/**
 *  There are many awesome community services that provide Ethereum
 *  nodes both for developers just starting out and for large-scale
 *  communities.
 *
 *  @_section: api/providers/thirdparty: Community Providers  [thirdparty]
 */
/**
 *  Providers which offer community credentials should extend this
 *  to notify any interested consumers whether community credentials
 *  are in-use.
 */
export interface CommunityResourcable {
    /**
     *  Returns true if the instance is connected using the community
     *  credentials.
     */
    isCommunityResource(): boolean;
}
/**
 *  Displays a warning in the console when the community resource is
 *  being used too heavily by the app, recommending the developer
 *  acquire their own credentials instead of using the community
 *  credentials.
 *
 *  The notification will only occur once per service.
 */
export declare function showThrottleMessage(service: string): void;
//# sourceMappingURL=community.d.ts.map