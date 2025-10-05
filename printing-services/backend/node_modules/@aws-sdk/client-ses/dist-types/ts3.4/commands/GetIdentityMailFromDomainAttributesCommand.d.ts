import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  GetIdentityMailFromDomainAttributesRequest,
  GetIdentityMailFromDomainAttributesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetIdentityMailFromDomainAttributesCommandInput
  extends GetIdentityMailFromDomainAttributesRequest {}
export interface GetIdentityMailFromDomainAttributesCommandOutput
  extends GetIdentityMailFromDomainAttributesResponse,
    __MetadataBearer {}
declare const GetIdentityMailFromDomainAttributesCommand_base: {
  new (
    input: GetIdentityMailFromDomainAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityMailFromDomainAttributesCommandInput,
    GetIdentityMailFromDomainAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetIdentityMailFromDomainAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityMailFromDomainAttributesCommandInput,
    GetIdentityMailFromDomainAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetIdentityMailFromDomainAttributesCommand extends GetIdentityMailFromDomainAttributesCommand_base {
  protected static __types: {
    api: {
      input: GetIdentityMailFromDomainAttributesRequest;
      output: GetIdentityMailFromDomainAttributesResponse;
    };
    sdk: {
      input: GetIdentityMailFromDomainAttributesCommandInput;
      output: GetIdentityMailFromDomainAttributesCommandOutput;
    };
  };
}
