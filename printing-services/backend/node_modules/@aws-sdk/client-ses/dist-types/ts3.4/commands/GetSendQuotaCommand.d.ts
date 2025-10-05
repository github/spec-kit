import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetSendQuotaResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetSendQuotaCommandInput {}
export interface GetSendQuotaCommandOutput
  extends GetSendQuotaResponse,
    __MetadataBearer {}
declare const GetSendQuotaCommand_base: {
  new (
    input: GetSendQuotaCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetSendQuotaCommandInput,
    GetSendQuotaCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [GetSendQuotaCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    GetSendQuotaCommandInput,
    GetSendQuotaCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetSendQuotaCommand extends GetSendQuotaCommand_base {
  protected static __types: {
    api: {
      input: {};
      output: GetSendQuotaResponse;
    };
    sdk: {
      input: GetSendQuotaCommandInput;
      output: GetSendQuotaCommandOutput;
    };
  };
}
