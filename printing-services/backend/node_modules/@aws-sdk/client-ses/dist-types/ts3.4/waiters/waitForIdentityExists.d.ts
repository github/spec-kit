import { WaiterConfiguration, WaiterResult } from "@smithy/util-waiter";
import { GetIdentityVerificationAttributesCommandInput } from "../commands/GetIdentityVerificationAttributesCommand";
import { SESClient } from "../SESClient";
export declare const waitForIdentityExists: (
  params: WaiterConfiguration<SESClient>,
  input: GetIdentityVerificationAttributesCommandInput
) => Promise<WaiterResult>;
export declare const waitUntilIdentityExists: (
  params: WaiterConfiguration<SESClient>,
  input: GetIdentityVerificationAttributesCommandInput
) => Promise<WaiterResult>;
