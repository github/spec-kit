import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteReceiptFilterRequest,
  DeleteReceiptFilterResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteReceiptFilterCommandInput
  extends DeleteReceiptFilterRequest {}
export interface DeleteReceiptFilterCommandOutput
  extends DeleteReceiptFilterResponse,
    __MetadataBearer {}
declare const DeleteReceiptFilterCommand_base: {
  new (
    input: DeleteReceiptFilterCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteReceiptFilterCommandInput,
    DeleteReceiptFilterCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteReceiptFilterCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteReceiptFilterCommandInput,
    DeleteReceiptFilterCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteReceiptFilterCommand extends DeleteReceiptFilterCommand_base {
  protected static __types: {
    api: {
      input: DeleteReceiptFilterRequest;
      output: {};
    };
    sdk: {
      input: DeleteReceiptFilterCommandInput;
      output: DeleteReceiptFilterCommandOutput;
    };
  };
}
