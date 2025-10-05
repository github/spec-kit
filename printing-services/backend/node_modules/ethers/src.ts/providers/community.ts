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

// Show the throttle message only once per service
const shown: Set<string> = new Set();

/**
 *  Displays a warning in the console when the community resource is
 *  being used too heavily by the app, recommending the developer
 *  acquire their own credentials instead of using the community
 *  credentials.
 *
 *  The notification will only occur once per service.
 */
export function showThrottleMessage(service: string): void {
    if (shown.has(service)) { return; }
    shown.add(service);

    console.log("========= NOTICE =========")
    console.log(`Request-Rate Exceeded for ${ service } (this message will not be repeated)`);
    console.log("");
    console.log("The default API keys for each service are provided as a highly-throttled,");
    console.log("community resource for low-traffic projects and early prototyping.");
    console.log("");
    console.log("While your application will continue to function, we highly recommended");
    console.log("signing up for your own API keys to improve performance, increase your");
    console.log("request rate/limit and enable other perks, such as metrics and advanced APIs.");
    console.log("");
    console.log("For more details: https:/\/docs.ethers.org/api-keys/");
    console.log("==========================");
}
