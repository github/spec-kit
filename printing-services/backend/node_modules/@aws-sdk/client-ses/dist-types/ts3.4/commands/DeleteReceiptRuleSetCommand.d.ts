import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteReceiptRuleSetRequest,
  DeleteReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteReceiptRuleSetCommandInput
  extends DeleteReceiptRuleSetRequest {}
export interface DeleteReceiptRuleSetCommandOutput
  extends DeleteReceiptRuleSetResponse,
    __MetadataBearer {}
declare const DeleteReceiptRuleSetCommand_base: {
  new (
    input: DeleteReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteReceiptRuleSetCommandInput,
    DeleteReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteReceiptRuleSetCommandInput,
    DeleteReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteReceiptRuleSetCommand extends DeleteReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: DeleteReceiptRuleSetRequest;
      output: {};
    };
    sdk: {
      input: DeleteReceiptRuleSetCommandInput;
      output: DeleteReceiptRuleSetCommandOutput;
    };
  };
}
