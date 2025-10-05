import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteReceiptRuleRequest,
  DeleteReceiptRuleResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteReceiptRuleCommandInput
  extends DeleteReceiptRuleRequest {}
export interface DeleteReceiptRuleCommandOutput
  extends DeleteReceiptRuleResponse,
    __MetadataBearer {}
declare const DeleteReceiptRuleCommand_base: {
  new (
    input: DeleteReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteReceiptRuleCommandInput,
    DeleteReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteReceiptRuleCommandInput,
    DeleteReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteReceiptRuleCommand extends DeleteReceiptRuleCommand_base {
  protected static __types: {
    api: {
      input: DeleteReceiptRuleRequest;
      output: {};
    };
    sdk: {
      input: DeleteReceiptRuleCommandInput;
      output: DeleteReceiptRuleCommandOutput;
    };
  };
}
