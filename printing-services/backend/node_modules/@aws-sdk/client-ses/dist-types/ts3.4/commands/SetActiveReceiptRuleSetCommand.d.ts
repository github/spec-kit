import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetActiveReceiptRuleSetRequest,
  SetActiveReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetActiveReceiptRuleSetCommandInput
  extends SetActiveReceiptRuleSetRequest {}
export interface SetActiveReceiptRuleSetCommandOutput
  extends SetActiveReceiptRuleSetResponse,
    __MetadataBearer {}
declare const SetActiveReceiptRuleSetCommand_base: {
  new (
    input: SetActiveReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetActiveReceiptRuleSetCommandInput,
    SetActiveReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [SetActiveReceiptRuleSetCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    SetActiveReceiptRuleSetCommandInput,
    SetActiveReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetActiveReceiptRuleSetCommand extends SetActiveReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: SetActiveReceiptRuleSetRequest;
      output: {};
    };
    sdk: {
      input: SetActiveReceiptRuleSetCommandInput;
      output: SetActiveReceiptRuleSetCommandOutput;
    };
  };
}
