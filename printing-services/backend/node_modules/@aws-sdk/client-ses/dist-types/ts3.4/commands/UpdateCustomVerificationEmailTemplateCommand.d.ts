import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateCustomVerificationEmailTemplateRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateCustomVerificationEmailTemplateCommandInput
  extends UpdateCustomVerificationEmailTemplateRequest {}
export interface UpdateCustomVerificationEmailTemplateCommandOutput
  extends __MetadataBearer {}
declare const UpdateCustomVerificationEmailTemplateCommand_base: {
  new (
    input: UpdateCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateCustomVerificationEmailTemplateCommandInput,
    UpdateCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateCustomVerificationEmailTemplateCommandInput,
    UpdateCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateCustomVerificationEmailTemplateCommand extends UpdateCustomVerificationEmailTemplateCommand_base {
  protected static __types: {
    api: {
      input: UpdateCustomVerificationEmailTemplateRequest;
      output: {};
    };
    sdk: {
      input: UpdateCustomVerificationEmailTemplateCommandInput;
      output: UpdateCustomVerificationEmailTemplateCommandOutput;
    };
  };
}
