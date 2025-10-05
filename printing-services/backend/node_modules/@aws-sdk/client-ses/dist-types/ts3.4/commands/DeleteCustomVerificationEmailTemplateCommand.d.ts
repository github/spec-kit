import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteCustomVerificationEmailTemplateRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteCustomVerificationEmailTemplateCommandInput
  extends DeleteCustomVerificationEmailTemplateRequest {}
export interface DeleteCustomVerificationEmailTemplateCommandOutput
  extends __MetadataBearer {}
declare const DeleteCustomVerificationEmailTemplateCommand_base: {
  new (
    input: DeleteCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteCustomVerificationEmailTemplateCommandInput,
    DeleteCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteCustomVerificationEmailTemplateCommandInput,
    DeleteCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteCustomVerificationEmailTemplateCommand extends DeleteCustomVerificationEmailTemplateCommand_base {
  protected static __types: {
    api: {
      input: DeleteCustomVerificationEmailTemplateRequest;
      output: {};
    };
    sdk: {
      input: DeleteCustomVerificationEmailTemplateCommandInput;
      output: DeleteCustomVerificationEmailTemplateCommandOutput;
    };
  };
}
