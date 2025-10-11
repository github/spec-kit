import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetAccountSendingEnabledResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetAccountSendingEnabledCommandInput {}
export interface GetAccountSendingEnabledCommandOutput
  extends GetAccountSendingEnabledResponse,
    __MetadataBearer {}
declare const GetAccountSendingEnabledCommand_base: {
  new (
    input: GetAccountSendingEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetAccountSendingEnabledCommandInput,
    GetAccountSendingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [GetAccountSendingEnabledCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    GetAccountSendingEnabledCommandInput,
    GetAccountSendingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetAccountSendingEnabledCommand extends GetAccountSendingEnabledCommand_base {
  protected static __types: {
    api: {
      input: {};
      output: GetAccountSendingEnabledResponse;
    };
    sdk: {
      input: GetAccountSendingEnabledCommandInput;
      output: GetAccountSendingEnabledCommandOutput;
    };
  };
}
