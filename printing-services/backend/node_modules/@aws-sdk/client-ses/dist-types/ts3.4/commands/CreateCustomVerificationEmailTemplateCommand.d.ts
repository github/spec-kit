import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { CreateCustomVerificationEmailTemplateRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateCustomVerificationEmailTemplateCommandInput
  extends CreateCustomVerificationEmailTemplateRequest {}
export interface CreateCustomVerificationEmailTemplateCommandOutput
  extends __MetadataBearer {}
declare const CreateCustomVerificationEmailTemplateCommand_base: {
  new (
    input: CreateCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateCustomVerificationEmailTemplateCommandInput,
    CreateCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateCustomVerificationEmailTemplateCommandInput,
    CreateCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateCustomVerificationEmailTemplateCommand extends CreateCustomVerificationEmailTemplateCommand_base {
  protected static __types: {
    api: {
      input: CreateCustomVerificationEmailTemplateRequest;
      output: {};
    };
    sdk: {
      input: CreateCustomVerificationEmailTemplateCommandInput;
      output: CreateCustomVerificationEmailTemplateCommandOutput;
    };
  };
}
