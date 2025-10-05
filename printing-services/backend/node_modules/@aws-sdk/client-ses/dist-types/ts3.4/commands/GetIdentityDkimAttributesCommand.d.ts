import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  GetIdentityDkimAttributesRequest,
  GetIdentityDkimAttributesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetIdentityDkimAttributesCommandInput
  extends GetIdentityDkimAttributesRequest {}
export interface GetIdentityDkimAttributesCommandOutput
  extends GetIdentityDkimAttributesResponse,
    __MetadataBearer {}
declare const GetIdentityDkimAttributesCommand_base: {
  new (
    input: GetIdentityDkimAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityDkimAttributesCommandInput,
    GetIdentityDkimAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetIdentityDkimAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityDkimAttributesCommandInput,
    GetIdentityDkimAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetIdentityDkimAttributesCommand extends GetIdentityDkimAttributesCommand_base {
  protected static __types: {
    api: {
      input: GetIdentityDkimAttributesRequest;
      output: GetIdentityDkimAttributesResponse;
    };
    sdk: {
      input: GetIdentityDkimAttributesCommandInput;
      output: GetIdentityDkimAttributesCommandOutput;
    };
  };
}
