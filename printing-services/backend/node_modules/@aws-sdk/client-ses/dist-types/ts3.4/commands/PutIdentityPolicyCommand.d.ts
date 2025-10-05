import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  PutIdentityPolicyRequest,
  PutIdentityPolicyResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface PutIdentityPolicyCommandInput
  extends PutIdentityPolicyRequest {}
export interface PutIdentityPolicyCommandOutput
  extends PutIdentityPolicyResponse,
    __MetadataBearer {}
declare const PutIdentityPolicyCommand_base: {
  new (
    input: PutIdentityPolicyCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    PutIdentityPolicyCommandInput,
    PutIdentityPolicyCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: PutIdentityPolicyCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    PutIdentityPolicyCommandInput,
    PutIdentityPolicyCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class PutIdentityPolicyCommand extends PutIdentityPolicyCommand_base {
  protected static __types: {
    api: {
      input: PutIdentityPolicyRequest;
      output: {};
    };
    sdk: {
      input: PutIdentityPolicyCommandInput;
      output: PutIdentityPolicyCommandOutput;
    };
  };
}
