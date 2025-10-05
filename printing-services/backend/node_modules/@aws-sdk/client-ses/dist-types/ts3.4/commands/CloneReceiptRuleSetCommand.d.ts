import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CloneReceiptRuleSetRequest,
  CloneReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CloneReceiptRuleSetCommandInput
  extends CloneReceiptRuleSetRequest {}
export interface CloneReceiptRuleSetCommandOutput
  extends CloneReceiptRuleSetResponse,
    __MetadataBearer {}
declare const CloneReceiptRuleSetCommand_base: {
  new (
    input: CloneReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CloneReceiptRuleSetCommandInput,
    CloneReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CloneReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CloneReceiptRuleSetCommandInput,
    CloneReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CloneReceiptRuleSetCommand extends CloneReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: CloneReceiptRuleSetRequest;
      output: {};
    };
    sdk: {
      input: CloneReceiptRuleSetCommandInput;
      output: CloneReceiptRuleSetCommandOutput;
    };
  };
}
