// @ts-nocheck
/* eslint-disable */
/* tslint:disable */
/* prettier-ignore-start */
/** @jsxRuntime classic */
/** @jsx createPlasmicElementProxy */
/** @jsxFrag React.Fragment */
// This class is auto-generated by Plasmic; please do not edit!
// Plasmic Project: mXv5TZ5SUPGRneH9RoMn6q
// Component: rgvwcoUrD14Pp
import * as React from "react";
import * as p from "@plasmicapp/react-web";
import {
  hasVariant,
  classNames,
  createPlasmicElementProxy,
  deriveRenderOpts,
  ensureGlobalVariants
} from "@plasmicapp/react-web";
import MenuButton from "../../MenuButton"; // plasmic-import: fd0a48CHFpLDW/component
import Button from "../../Button"; // plasmic-import: 3egWRKWeo74/component
import IconLink from "../../IconLink"; // plasmic-import: sBgr46KDuJYZz/component
import SearchInputComponent from "../../SearchInputComponent"; // plasmic-import: 1ReshBZ5EGa/component
import LinkButton from "../../LinkButton"; // plasmic-import: tr5phcLQqCoEx/component
import { useScreenVariants as useScreenVariantsthj0P9Nxeh81I } from "./PlasmicGlobalVariant__Screen"; // plasmic-import: thj0p9NXEH81i/globalVariant
import "@plasmicapp/react-web/lib/plasmic.css";
import "../plasmic__default_style.css"; // plasmic-import: global/defaultcss
import "../library_plasmic_color_type/plasmic_library_plasmic_color_type.css"; // plasmic-import: seaQhLVS4bbjiGvJJrRwyL/projectcss
import "./plasmic_canvas_app_explorer.css"; // plasmic-import: mXv5TZ5SUPGRneH9RoMn6q/projectcss
import "./PlasmicHeader.css"; // plasmic-import: rgvwcoUrD14Pp/css
import SearchIcon from "./icons/PlasmicIcon__Search"; // plasmic-import: XYsIQokGkGcBz/icon
import CogIcon from "./icons/PlasmicIcon__Cog"; // plasmic-import: jxNUPxdPJcbB1/icon

export const PlasmicHeader__VariantProps = new Array(
  "expanded",
  "withSearchBar",
  "noSearchBarOrSettings",
  "searchBarAndCategories"
);

export const PlasmicHeader__ArgProps = new Array("searchInputSlot");

function PlasmicHeader__RenderFunc(props) {
  const { variants, args, overrides, forNode } = props;
  const globalVariants = ensureGlobalVariants({
    screen: useScreenVariantsthj0P9Nxeh81I()
  });

  return (
    <div
      data-plasmic-name={"root"}
      data-plasmic-override={overrides.root}
      data-plasmic-root={true}
      data-plasmic-for-node={forNode}
      className={classNames(
        "plasmic_default__all",
        "plasmic_default__div",
        "root_reset_mXv5TZ5SUPGRneH9RoMn6q",
        "plasmic_default_styles",
        "plasmic_tokens",
        "plasmic_tokens",
        "Header__root__r4I1P",
        {
          Header__rootexpanded__r4I1Pvp9H7: hasVariant(
            variants,
            "expanded",
            "expanded"
          )
        }
      )}
    >
      <p.Stack
        as={"div"}
        hasGap={true}
        className={classNames(
          "plasmic_default__all",
          "plasmic_default__div",
          "Header__freeBox__ikq92",
          {
            Header__freeBoxnoSearchBarOrSettings__ikq92I2VQm: hasVariant(
              variants,
              "noSearchBarOrSettings",
              "noSearchBarOrSettings"
            ),

            Header__freeBoxsearchBarAndCategories__ikq92B146L: hasVariant(
              variants,
              "searchBarAndCategories",
              "searchBarAndCategories"
            ),

            Header__freeBoxwithSearchBar__ikq928Xp20: hasVariant(
              variants,
              "withSearchBar",
              "withSearchBar"
            )
          }
        )}
      >
        {(hasVariant(globalVariants, "screen", "mobile") ? true : false) ? (
          <MenuButton
            data-plasmic-name={"menuButton"}
            data-plasmic-override={overrides.menuButton}
            className={classNames(
              "__wab_instance",
              "Header__menuButton__bmiow",
              {
                Header__menuButtonexpanded__bmiowVp9H7: hasVariant(
                  variants,
                  "expanded",
                  "expanded"
                )
              }
            )}
            expanded={
              hasVariant(variants, "expanded", "expanded") &&
              hasVariant(globalVariants, "screen", "mobile")
                ? true
                : undefined
            }
          />
        ) : null}

        <div
          data-plasmic-name={"text"}
          data-plasmic-override={overrides.text}
          className={classNames(
            "plasmic_default__all",
            "plasmic_default__div",
            "__wab_text",
            "Header__text__keObZ"
          )}
        >
          {"Canvas App Explorer"}
        </div>

        {false ? (
          <input
            className={classNames(
              "plasmic_default__all",
              "plasmic_default__input",
              "Header__textInput__cDxmy"
            )}
            placeholder={"Some placeholder"}
            size={1}
            type={"text"}
            value={"Some value"}
          />
        ) : null}
        {false ? (
          <input
            className={classNames(
              "plasmic_default__all",
              "plasmic_default__input",
              "Header__textInput__mlQAu"
            )}
            placeholder={"Some placeholder"}
            size={1}
            type={"text"}
            value={"Some value"}
          />
        ) : null}
        {(
          hasVariant(
            variants,
            "searchBarAndCategories",
            "searchBarAndCategories"
          )
            ? true
            : true
        ) ? (
          <div
            data-plasmic-name={"columns"}
            data-plasmic-override={overrides.columns}
            className={classNames(
              "plasmic_default__all",
              "plasmic_default__div",
              "Header__columns__fymsz",
              {
                Header__columnssearchBarAndCategories__fymszb146L: hasVariant(
                  variants,
                  "searchBarAndCategories",
                  "searchBarAndCategories"
                )
              }
            )}
          >
            {(
              hasVariant(
                variants,
                "searchBarAndCategories",
                "searchBarAndCategories"
              )
                ? true
                : true
            ) ? (
              <div
                className={classNames(
                  "plasmic_default__all",
                  "plasmic_default__div",
                  "Header__column__lbnzr",
                  {
                    Header__columnsearchBarAndCategories__lbnzrb146L:
                      hasVariant(
                        variants,
                        "searchBarAndCategories",
                        "searchBarAndCategories"
                      )
                  }
                )}
              >
                <Button
                  className={classNames(
                    "__wab_instance",
                    "Header__button___5RsFq",
                    {
                      Header__buttonsearchBarAndCategories___5RsFQb146L:
                        hasVariant(
                          variants,
                          "searchBarAndCategories",
                          "searchBarAndCategories"
                        )
                    }
                  )}
                />
              </div>
            ) : null}
            {(
              hasVariant(
                variants,
                "searchBarAndCategories",
                "searchBarAndCategories"
              )
                ? true
                : true
            ) ? (
              <div
                className={classNames(
                  "plasmic_default__all",
                  "plasmic_default__div",
                  "Header__column__ah9Na",
                  {
                    Header__columnsearchBarAndCategories__ah9NAb146L:
                      hasVariant(
                        variants,
                        "searchBarAndCategories",
                        "searchBarAndCategories"
                      )
                  }
                )}
              >
                <Button
                  className={classNames(
                    "__wab_instance",
                    "Header__button__z29JG",
                    {
                      Header__buttonsearchBarAndCategories__z29JGb146L:
                        hasVariant(
                          variants,
                          "searchBarAndCategories",
                          "searchBarAndCategories"
                        )
                    }
                  )}
                />
              </div>
            ) : null}
          </div>
        ) : null}

        <p.Stack
          as={"div"}
          hasGap={true}
          className={classNames(
            "plasmic_default__all",
            "plasmic_default__div",
            "Header__freeBox__zcEqf",
            {
              Header__freeBoxsearchBarAndCategories__zcEqfb146L: hasVariant(
                variants,
                "searchBarAndCategories",
                "searchBarAndCategories"
              ),

              Header__freeBoxwithSearchBar__zcEqf8Xp20: hasVariant(
                variants,
                "withSearchBar",
                "withSearchBar"
              )
            }
          )}
        >
          {(
            hasVariant(
              variants,
              "searchBarAndCategories",
              "searchBarAndCategories"
            )
              ? false
              : hasVariant(variants, "withSearchBar", "withSearchBar")
              ? true
              : true
          ) ? (
            <IconLink
              className={classNames(
                "__wab_instance",
                "Header__iconLink__rda3A",
                {
                  Header__iconLinknoSearchBarOrSettings__rda3Ai2VQm: hasVariant(
                    variants,
                    "noSearchBarOrSettings",
                    "noSearchBarOrSettings"
                  ),

                  Header__iconLinksearchBarAndCategories__rda3Ab146L:
                    hasVariant(
                      variants,
                      "searchBarAndCategories",
                      "searchBarAndCategories"
                    ),

                  Header__iconLinkwithSearchBar__rda3A8Xp20: hasVariant(
                    variants,
                    "withSearchBar",
                    "withSearchBar"
                  )
                }
              )}
              icon={
                (
                  hasVariant(
                    variants,
                    "noSearchBarOrSettings",
                    "noSearchBarOrSettings"
                  )
                    ? false
                    : true
                ) ? (
                  <SearchIcon
                    className={classNames(
                      "plasmic_default__all",
                      "plasmic_default__svg",
                      "Header__svg___7Ic5E",
                      {
                        Header__svgnoSearchBarOrSettings___7Ic5Ei2VQm:
                          hasVariant(
                            variants,
                            "noSearchBarOrSettings",
                            "noSearchBarOrSettings"
                          ),

                        Header__svgwithSearchBar___7Ic5E8Xp20: hasVariant(
                          variants,
                          "withSearchBar",
                          "withSearchBar"
                        )
                      }
                    )}
                    role={"img"}
                  />
                ) : null
              }
            />
          ) : null}
          {(
            hasVariant(
              variants,
              "noSearchBarOrSettings",
              "noSearchBarOrSettings"
            )
              ? false
              : true
          )
            ? p.renderPlasmicSlot({
                defaultContents: (
                  <SearchInputComponent
                    className={classNames(
                      "__wab_instance",
                      "Header__searchInputComponent___4TRpX"
                    )}
                    withSearchBar={true}
                  />
                ),

                value: args.searchInputSlot
              })
            : null}
          {(
            hasVariant(
              variants,
              "searchBarAndCategories",
              "searchBarAndCategories"
            )
              ? false
              : hasVariant(
                  variants,
                  "noSearchBarOrSettings",
                  "noSearchBarOrSettings"
                )
              ? false
              : hasVariant(variants, "withSearchBar", "withSearchBar")
              ? false
              : true
          ) ? (
            <IconLink
              className={classNames(
                "__wab_instance",
                "Header__iconLink__pu1Ei",
                {
                  Header__iconLinknoSearchBarOrSettings__pu1Eii2VQm: hasVariant(
                    variants,
                    "noSearchBarOrSettings",
                    "noSearchBarOrSettings"
                  ),

                  Header__iconLinksearchBarAndCategories__pu1Eib146L:
                    hasVariant(
                      variants,
                      "searchBarAndCategories",
                      "searchBarAndCategories"
                    ),

                  Header__iconLinkwithSearchBar__pu1Ei8Xp20: hasVariant(
                    variants,
                    "withSearchBar",
                    "withSearchBar"
                  )
                }
              )}
              icon={
                (
                  hasVariant(
                    variants,
                    "searchBarAndCategories",
                    "searchBarAndCategories"
                  )
                    ? false
                    : true
                ) ? (
                  <CogIcon
                    className={classNames(
                      "plasmic_default__all",
                      "plasmic_default__svg",
                      "Header__svg__agh0S",
                      {
                        Header__svgsearchBarAndCategories__agh0Sb146L:
                          hasVariant(
                            variants,
                            "searchBarAndCategories",
                            "searchBarAndCategories"
                          )
                      }
                    )}
                    role={"img"}
                  />
                ) : null
              }
            />
          ) : null}
        </p.Stack>
      </p.Stack>

      {(
        hasVariant(variants, "expanded", "expanded") &&
        hasVariant(globalVariants, "screen", "mobile")
          ? true
          : false
      ) ? (
        <div
          className={classNames(
            "plasmic_default__all",
            "plasmic_default__div",
            "Header__freeBox__qIiNj",
            {
              Header__freeBoxexpanded__qIiNjVp9H7: hasVariant(
                variants,
                "expanded",
                "expanded"
              )
            }
          )}
        >
          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__bhzkI"
            )}
            text={"Home"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__xdYja"
            )}
            text={"New Arrival"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__nKvUv"
            )}
            text={"Features"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__hk6Zt"
            )}
            text={"Blog"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__wWLqi"
            )}
            text={"Contact"}
            type={"blankGray"}
          />
        </div>
      ) : null}
    </div>
  );
}

const PlasmicDescendants = {
  root: ["root", "menuButton", "text", "columns"],
  menuButton: ["menuButton"],
  text: ["text"],
  columns: ["columns"]
};

function makeNodeComponent(nodeName) {
  const func = function (props) {
    const { variants, args, overrides } = deriveRenderOpts(props, {
      name: nodeName,
      descendantNames: [...PlasmicDescendants[nodeName]],
      internalArgPropNames: PlasmicHeader__ArgProps,
      internalVariantPropNames: PlasmicHeader__VariantProps
    });

    return PlasmicHeader__RenderFunc({
      variants,
      args,
      overrides,
      forNode: nodeName
    });
  };
  if (nodeName === "root") {
    func.displayName = "PlasmicHeader";
  } else {
    func.displayName = `PlasmicHeader.${nodeName}`;
  }
  return func;
}

export const PlasmicHeader = Object.assign(
  // Top-level PlasmicHeader renders the root element
  makeNodeComponent("root"),
  {
    // Helper components rendering sub-elements
    menuButton: makeNodeComponent("menuButton"),
    text: makeNodeComponent("text"),
    columns: makeNodeComponent("columns"),
    // Metadata about props expected for PlasmicHeader
    internalVariantProps: PlasmicHeader__VariantProps,
    internalArgProps: PlasmicHeader__ArgProps
  }
);

export default PlasmicHeader;
/* prettier-ignore-end */
