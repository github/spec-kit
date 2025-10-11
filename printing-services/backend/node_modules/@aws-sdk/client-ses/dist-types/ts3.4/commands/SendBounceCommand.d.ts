import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SendBounceRequest, SendBounceResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SendBounceCommandInput extends SendBounceRequest {}
export interface SendBounceCommandOutput
  extends SendBounceResponse,
    __MetadataBearer {}
declare const SendBounceCommand_base: {
  new (
    input: SendBounceCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendBounceCommandInput,
    SendBounceCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SendBounceCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendBounceCommandInput,
    SendBounceCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SendBounceCommand extends SendBounceCommand_base {
  protected static __types: {
    api: {
      input: SendBounceRequest;
      output: SendBounceResponse;
    };
    sdk: {
      input: SendBounceCommandInput;
      output: SendBounceCommandOutput;
    };
  };
}
