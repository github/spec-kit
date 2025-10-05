import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetSendStatisticsResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetSendStatisticsCommandInput {}
export interface GetSendStatisticsCommandOutput
  extends GetSendStatisticsResponse,
    __MetadataBearer {}
declare const GetSendStatisticsCommand_base: {
  new (
    input: GetSendStatisticsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetSendStatisticsCommandInput,
    GetSendStatisticsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [GetSendStatisticsCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    GetSendStatisticsCommandInput,
    GetSendStatisticsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetSendStatisticsCommand extends GetSendStatisticsCommand_base {
  protected static __types: {
    api: {
      input: {};
      output: GetSendStatisticsResponse;
    };
    sdk: {
      input: GetSendStatisticsCommandInput;
      output: GetSendStatisticsCommandOutput;
    };
  };
}
