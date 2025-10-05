import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteTemplateRequest,
  DeleteTemplateResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteTemplateCommandInput extends DeleteTemplateRequest {}
export interface DeleteTemplateCommandOutput
  extends DeleteTemplateResponse,
    __MetadataBearer {}
declare const DeleteTemplateCommand_base: {
  new (
    input: DeleteTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteTemplateCommandInput,
    DeleteTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteTemplateCommandInput,
    DeleteTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteTemplateCommand extends DeleteTemplateCommand_base {
  protected static __types: {
    api: {
      input: DeleteTemplateRequest;
      output: {};
    };
    sdk: {
      input: DeleteTemplateCommandInput;
      output: DeleteTemplateCommandOutput;
    };
  };
}
