import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  PutConfigurationSetDeliveryOptionsRequest,
  PutConfigurationSetDeliveryOptionsResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface PutConfigurationSetDeliveryOptionsCommandInput
  extends PutConfigurationSetDeliveryOptionsRequest {}
export interface PutConfigurationSetDeliveryOptionsCommandOutput
  extends PutConfigurationSetDeliveryOptionsResponse,
    __MetadataBearer {}
declare const PutConfigurationSetDeliveryOptionsCommand_base: {
  new (
    input: PutConfigurationSetDeliveryOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    PutConfigurationSetDeliveryOptionsCommandInput,
    PutConfigurationSetDeliveryOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: PutConfigurationSetDeliveryOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    PutConfigurationSetDeliveryOptionsCommandInput,
    PutConfigurationSetDeliveryOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class PutConfigurationSetDeliveryOptionsCommand extends PutConfigurationSetDeliveryOptionsCommand_base {
  protected static __types: {
    api: {
      input: PutConfigurationSetDeliveryOptionsRequest;
      output: {};
    };
    sdk: {
      input: PutConfigurationSetDeliveryOptionsCommandInput;
      output: PutConfigurationSetDeliveryOptionsCommandOutput;
    };
  };
}
