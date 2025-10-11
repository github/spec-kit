import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  GetIdentityNotificationAttributesRequest,
  GetIdentityNotificationAttributesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetIdentityNotificationAttributesCommandInput
  extends GetIdentityNotificationAttributesRequest {}
export interface GetIdentityNotificationAttributesCommandOutput
  extends GetIdentityNotificationAttributesResponse,
    __MetadataBearer {}
declare const GetIdentityNotificationAttributesCommand_base: {
  new (
    input: GetIdentityNotificationAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityNotificationAttributesCommandInput,
    GetIdentityNotificationAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetIdentityNotificationAttributesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetIdentityNotificationAttributesCommandInput,
    GetIdentityNotificationAttributesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetIdentityNotificationAttributesCommand extends GetIdentityNotificationAttributesCommand_base {
  protected static __types: {
    api: {
      input: GetIdentityNotificationAttributesRequest;
      output: GetIdentityNotificationAttributesResponse;
    };
    sdk: {
      input: GetIdentityNotificationAttributesCommandInput;
      output: GetIdentityNotificationAttributesCommandOutput;
    };
  };
}
