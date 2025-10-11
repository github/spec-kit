import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ListIdentityPoliciesRequest,
  ListIdentityPoliciesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ListIdentityPoliciesCommandInput
  extends ListIdentityPoliciesRequest {}
export interface ListIdentityPoliciesCommandOutput
  extends ListIdentityPoliciesResponse,
    __MetadataBearer {}
declare const ListIdentityPoliciesCommand_base: {
  new (
    input: ListIdentityPoliciesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListIdentityPoliciesCommandInput,
    ListIdentityPoliciesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: ListIdentityPoliciesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListIdentityPoliciesCommandInput,
    ListIdentityPoliciesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListIdentityPoliciesCommand extends ListIdentityPoliciesCommand_base {
  protected static __types: {
    api: {
      input: ListIdentityPoliciesRequest;
      output: ListIdentityPoliciesResponse;
    };
    sdk: {
      input: ListIdentityPoliciesCommandInput;
      output: ListIdentityPoliciesCommandOutput;
    };
  };
}
