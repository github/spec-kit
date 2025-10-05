import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  UpdateTemplateRequest,
  UpdateTemplateResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateTemplateCommandInput extends UpdateTemplateRequest {}
export interface UpdateTemplateCommandOutput
  extends UpdateTemplateResponse,
    __MetadataBearer {}
declare const UpdateTemplateCommand_base: {
  new (
    input: UpdateTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateTemplateCommandInput,
    UpdateTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateTemplateCommandInput,
    UpdateTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateTemplateCommand extends UpdateTemplateCommand_base {
  protected static __types: {
    api: {
      input: UpdateTemplateRequest;
      output: {};
    };
    sdk: {
      input: UpdateTemplateCommandInput;
      output: UpdateTemplateCommandOutput;
    };
  };
}
