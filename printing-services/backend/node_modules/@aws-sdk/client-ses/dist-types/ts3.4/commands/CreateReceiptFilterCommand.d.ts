import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateReceiptFilterRequest,
  CreateReceiptFilterResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateReceiptFilterCommandInput
  extends CreateReceiptFilterRequest {}
export interface CreateReceiptFilterCommandOutput
  extends CreateReceiptFilterResponse,
    __MetadataBearer {}
declare const CreateReceiptFilterCommand_base: {
  new (
    input: CreateReceiptFilterCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateReceiptFilterCommandInput,
    CreateReceiptFilterCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateReceiptFilterCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateReceiptFilterCommandInput,
    CreateReceiptFilterCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateReceiptFilterCommand extends CreateReceiptFilterCommand_base {
  protected static __types: {
    api: {
      input: CreateReceiptFilterRequest;
      output: {};
    };
    sdk: {
      input: CreateReceiptFilterCommandInput;
      output: CreateReceiptFilterCommandOutput;
    };
  };
}
