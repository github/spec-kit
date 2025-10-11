import { checkExceptions, createWaiter, WaiterState } from "@smithy/util-waiter";
import { GetIdentityVerificationAttributesCommand, } from "../commands/GetIdentityVerificationAttributesCommand";
const checkState = async (client, input) => {
    let reason;
    try {
        const result = await client.send(new GetIdentityVerificationAttributesCommand(input));
        reason = result;
        try {
            const returnComparator = () => {
                const objectProjection_2 = Object.values(result.VerificationAttributes).map((element_1) => {
                    return element_1.VerificationStatus;
                });
                return objectProjection_2;
            };
            let allStringEq_4 = returnComparator().length > 0;
            for (const element_3 of returnComparator()) {
                allStringEq_4 = allStringEq_4 && element_3 == "Success";
            }
            if (allStringEq_4) {
                return { state: WaiterState.SUCCESS, reason };
            }
        }
        catch (e) { }
    }
    catch (exception) {
        reason = exception;
    }
    return { state: WaiterState.RETRY, reason };
};
export const waitForIdentityExists = async (params, input) => {
    const serviceDefaults = { minDelay: 3, maxDelay: 120 };
    return createWaiter({ ...serviceDefaults, ...params }, input, checkState);
};
export const waitUntilIdentityExists = async (params, input) => {
    const serviceDefaults = { minDelay: 3, maxDelay: 120 };
    const result = await createWaiter({ ...serviceDefaults, ...params }, input, checkState);
    return checkExceptions(result);
};
