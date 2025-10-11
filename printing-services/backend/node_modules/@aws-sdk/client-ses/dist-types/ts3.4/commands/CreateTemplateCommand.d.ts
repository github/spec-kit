import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateTemplateRequest,
  CreateTemplateResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateTemplateCommandInput extends CreateTemplateRequest {}
export interface CreateTemplateCommandOutput
  extends CreateTemplateResponse,
    __MetadataBearer {}
declare const CreateTemplateCommand_base: {
  new (
    input: CreateTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateTemplateCommandInput,
    CreateTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateTemplateCommandInput,
    CreateTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateTemplateCommand extends CreateTemplateCommand_base {
  protected static __types: {
    api: {
      input: CreateTemplateRequest;
      output: {};
    };
    sdk: {
      input: CreateTemplateCommandInput;
      output: CreateTemplateCommandOutput;
    };
  };
}
