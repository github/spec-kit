import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  UpdateReceiptRuleRequest,
  UpdateReceiptRuleResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateReceiptRuleCommandInput
  extends UpdateReceiptRuleRequest {}
export interface UpdateReceiptRuleCommandOutput
  extends UpdateReceiptRuleResponse,
    __MetadataBearer {}
declare const UpdateReceiptRuleCommand_base: {
  new (
    input: UpdateReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateReceiptRuleCommandInput,
    UpdateReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateReceiptRuleCommandInput,
    UpdateReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateReceiptRuleCommand extends UpdateReceiptRuleCommand_base {
  protected static __types: {
    api: {
      input: UpdateReceiptRuleRequest;
      output: {};
    };
    sdk: {
      input: UpdateReceiptRuleCommandInput;
      output: UpdateReceiptRuleCommandOutput;
    };
  };
}
