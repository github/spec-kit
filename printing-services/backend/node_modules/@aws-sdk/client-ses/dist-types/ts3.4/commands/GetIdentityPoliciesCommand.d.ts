import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  GetIdentityPoliciesRequest,
  GetIdentityPoliciesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetIdentityPoliciesCommandInput
  extends GetIdentityPoliciesRequest {}
export interface GetIdentityPoliciesCommandOutput
  extends GetIdentityPoliciesResponse,
    __MetadataBearer {}
declare const GetIdentityPoliciesCommand_base: {
  new (
    input: GetIdentityPoliciesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityPoliciesCommandInput,
    GetIdentityPoliciesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetIdentityPoliciesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityPoliciesCommandInput,
    GetIdentityPoliciesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetIdentityPoliciesCommand extends GetIdentityPoliciesCommand_base {
  protected static __types: {
    api: {
      input: GetIdentityPoliciesRequest;
      output: GetIdentityPoliciesResponse;
    };
    sdk: {
      input: GetIdentityPoliciesCommandInput;
      output: GetIdentityPoliciesCommandOutput;
    };
  };
}
