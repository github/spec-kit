import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SendBulkTemplatedEmailRequest,
  SendBulkTemplatedEmailResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SendBulkTemplatedEmailCommandInput
  extends SendBulkTemplatedEmailRequest {}
export interface SendBulkTemplatedEmailCommandOutput
  extends SendBulkTemplatedEmailResponse,
    __MetadataBearer {}
declare const SendBulkTemplatedEmailCommand_base: {
  new (
    input: SendBulkTemplatedEmailCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendBulkTemplatedEmailCommandInput,
    SendBulkTemplatedEmailCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SendBulkTemplatedEmailCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendBulkTemplatedEmailCommandInput,
    SendBulkTemplatedEmailCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SendBulkTemplatedEmailCommand extends SendBulkTemplatedEmailCommand_base {
  protected static __types: {
    api: {
      input: SendBulkTemplatedEmailRequest;
      output: SendBulkTemplatedEmailResponse;
    };
    sdk: {
      input: SendBulkTemplatedEmailCommandInput;
      output: SendBulkTemplatedEmailCommandOutput;
    };
  };
}
