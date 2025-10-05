import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetReceiptRulePositionRequest,
  SetReceiptRulePositionResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetReceiptRulePositionCommandInput
  extends SetReceiptRulePositionRequest {}
export interface SetReceiptRulePositionCommandOutput
  extends SetReceiptRulePositionResponse,
    __MetadataBearer {}
declare const SetReceiptRulePositionCommand_base: {
  new (
    input: SetReceiptRulePositionCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetReceiptRulePositionCommandInput,
    SetReceiptRulePositionCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SetReceiptRulePositionCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetReceiptRulePositionCommandInput,
    SetReceiptRulePositionCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetReceiptRulePositionCommand extends SetReceiptRulePositionCommand_base {
  protected static __types: {
    api: {
      input: SetReceiptRulePositionRequest;
      output: {};
    };
    sdk: {
      input: SetReceiptRulePositionCommandInput;
      output: SetReceiptRulePositionCommandOutput;
    };
  };
}
