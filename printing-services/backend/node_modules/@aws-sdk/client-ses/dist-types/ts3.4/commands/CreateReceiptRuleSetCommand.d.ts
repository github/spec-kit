import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateReceiptRuleSetRequest,
  CreateReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateReceiptRuleSetCommandInput
  extends CreateReceiptRuleSetRequest {}
export interface CreateReceiptRuleSetCommandOutput
  extends CreateReceiptRuleSetResponse,
    __MetadataBearer {}
declare const CreateReceiptRuleSetCommand_base: {
  new (
    input: CreateReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateReceiptRuleSetCommandInput,
    CreateReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateReceiptRuleSetCommandInput,
    CreateReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateReceiptRuleSetCommand extends CreateReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: CreateReceiptRuleSetRequest;
      output: {};
    };
    sdk: {
      input: CreateReceiptRuleSetCommandInput;
      output: CreateReceiptRuleSetCommandOutput;
    };
  };
}
