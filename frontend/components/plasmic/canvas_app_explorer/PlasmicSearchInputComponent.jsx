// @ts-nocheck
/* eslint-disable */
/* tslint:disable */
/* prettier-ignore-start */
/** @jsxRuntime classic */
/** @jsx createPlasmicElementProxy */
/** @jsxFrag React.Fragment */
// This class is auto-generated by Plasmic; please do not edit!
// Plasmic Project: mXv5TZ5SUPGRneH9RoMn6q
// Component: 1ReshBZ5EGa
import * as React from "react";
import {
  hasVariant,
  classNames,
  createPlasmicElementProxy,
  deriveRenderOpts
} from "@plasmicapp/react-web";
import "@plasmicapp/react-web/lib/plasmic.css";
import "../plasmic__default_style.css"; // plasmic-import: global/defaultcss
import "../library_plasmic_color_type/plasmic_library_plasmic_color_type.css"; // plasmic-import: seaQhLVS4bbjiGvJJrRwyL/projectcss
import "./plasmic_canvas_app_explorer.css"; // plasmic-import: mXv5TZ5SUPGRneH9RoMn6q/projectcss
import "./PlasmicSearchInputComponent.css"; // plasmic-import: 1ReshBZ5EGa/css

export const PlasmicSearchInputComponent__VariantProps = new Array(
  "withSearchBar"
);

export const PlasmicSearchInputComponent__ArgProps = new Array();

function PlasmicSearchInputComponent__RenderFunc(props) {
  const { variants, args, overrides, forNode } = props;
  return (
    hasVariant(variants, "withSearchBar", "withSearchBar") ? true : false
  ) ? (
    <input
      data-plasmic-name={"root"}
      data-plasmic-override={overrides.root}
      data-plasmic-root={true}
      data-plasmic-for-node={forNode}
      className={classNames(
        "plasmic_default__all",
        "plasmic_default__input",
        "root_reset_mXv5TZ5SUPGRneH9RoMn6q",
        "plasmic_default_styles",
        "plasmic_tokens",
        "plasmic_tokens",
        "SearchInputComponent__root__f4YV",
        {
          SearchInputComponent__rootwithSearchBar__f4YV6FlrH: hasVariant(
            variants,
            "withSearchBar",
            "withSearchBar"
          )
        }
      )}
      placeholder={
        hasVariant(variants, "withSearchBar", "withSearchBar")
          ? "filter by keyword"
          : "Some placeholder"
      }
      size={1}
      type={"text"}
      value={
        hasVariant(variants, "withSearchBar", "withSearchBar")
          ? ""
          : "Some value"
      }
    />
  ) : null;
}

const PlasmicDescendants = {
  root: ["root"]
};

function makeNodeComponent(nodeName) {
  const func = function (props) {
    const { variants, args, overrides } = deriveRenderOpts(props, {
      name: nodeName,
      descendantNames: [...PlasmicDescendants[nodeName]],
      internalArgPropNames: PlasmicSearchInputComponent__ArgProps,
      internalVariantPropNames: PlasmicSearchInputComponent__VariantProps
    });

    return PlasmicSearchInputComponent__RenderFunc({
      variants,
      args,
      overrides,
      forNode: nodeName
    });
  };
  if (nodeName === "root") {
    func.displayName = "PlasmicSearchInputComponent";
  } else {
    func.displayName = `PlasmicSearchInputComponent.${nodeName}`;
  }
  return func;
}

export const PlasmicSearchInputComponent = Object.assign(
  // Top-level PlasmicSearchInputComponent renders the root element
  makeNodeComponent("root"),
  {
    // Helper components rendering sub-elements
    // Metadata about props expected for PlasmicSearchInputComponent
    internalVariantProps: PlasmicSearchInputComponent__VariantProps,
    internalArgProps: PlasmicSearchInputComponent__ArgProps
  }
);

export default PlasmicSearchInputComponent;
/* prettier-ignore-end */
