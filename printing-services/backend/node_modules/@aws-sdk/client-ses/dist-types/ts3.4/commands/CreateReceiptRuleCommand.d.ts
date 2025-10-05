import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateReceiptRuleRequest,
  CreateReceiptRuleResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateReceiptRuleCommandInput
  extends CreateReceiptRuleRequest {}
export interface CreateReceiptRuleCommandOutput
  extends CreateReceiptRuleResponse,
    __MetadataBearer {}
declare const CreateReceiptRuleCommand_base: {
  new (
    input: CreateReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateReceiptRuleCommandInput,
    CreateReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateReceiptRuleCommandInput,
    CreateReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateReceiptRuleCommand extends CreateReceiptRuleCommand_base {
  protected static __types: {
    api: {
      input: CreateReceiptRuleRequest;
      output: {};
    };
    sdk: {
      input: CreateReceiptRuleCommandInput;
      output: CreateReceiptRuleCommandOutput;
    };
  };
}
