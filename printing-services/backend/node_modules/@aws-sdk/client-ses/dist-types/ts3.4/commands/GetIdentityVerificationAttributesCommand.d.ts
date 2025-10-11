import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  GetIdentityVerificationAttributesRequest,
  GetIdentityVerificationAttributesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetIdentityVerificationAttributesCommandInput
  extends GetIdentityVerificationAttributesRequest {}
export interface GetIdentityVerificationAttributesCommandOutput
  extends GetIdentityVerificationAttributesResponse,
    __MetadataBearer {}
declare const GetIdentityVerificationAttributesCommand_base: {
  new (
    input: GetIdentityVerificationAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityVerificationAttributesCommandInput,
    GetIdentityVerificationAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetIdentityVerificationAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityVerificationAttributesCommandInput,
    GetIdentityVerificationAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetIdentityVerificationAttributesCommand extends GetIdentityVerificationAttributesCommand_base {
  protected static __types: {
    api: {
      input: GetIdentityVerificationAttributesRequest;
      output: GetIdentityVerificationAttributesResponse;
    };
    sdk: {
      input: GetIdentityVerificationAttributesCommandInput;
      output: GetIdentityVerificationAttributesCommandOutput;
    };
  };
}
