// This is a skeleton starter React component generated by Plasmic.
// This file is owned by you, feel free to edit as you see fit.
import React, { useState } from "react";

import ExitLearnMoreButton from "./ExitLearnMoreButton";
import TitleLearnMoreButton from "./TitleLearnMoreButton";

import { PlasmicProductCard } from "./plasmic/canvas_app_explorer/PlasmicProductCard";

function ProductCard_(props, ref) {
  // Use PlasmicProductCard to render this component as it was
  // designed in Plasmic, by activating the appropriate variants,
  // attaching the appropriate event handlers, etc.  You
  // can also install whatever React hooks you need here to manage state or
  // fetch data.
  //
  // Props you can pass into PlasmicProductCard are:
  // 1. Variants you want to activate,
  // 2. Contents for slots you want to fill,
  // 3. Overrides for any named node in the component to attach behavior and data,
  // 4. Props to set on the root node.
  //
  // By default, we are just piping all ProductCardProps here, but feel free
  // to do whatever works for you.

  const { tool } = props;

  const [learnMoreActive, setLearnMoreActive] = useState(false);

  const commonProps = {
    root: { ref },
    logo: tool.logo_image
  };
  if (!learnMoreActive) {
    return (
      <PlasmicProductCard
        {...commonProps}
        withoutScreenshotButtons={true}
        title={tool.name}
        description={<span dangerouslySetInnerHTML={{ __html: tool.short_description }} />}
        learnMoreSlot={
          <TitleLearnMoreButton
            onClick={(e) => {
              e.preventDefault();
              setLearnMoreActive(true)
            }}
          >
            {tool.name}
          </TitleLearnMoreButton>
        }
        ratings={
          null // <Ratings numReviews={"(45 Review)"} stars={"five"} />
        }
      />
    )
  } else {
    return (
      <PlasmicProductCard // Other side of the Learn More If
        {...commonProps}
        learnMoreWithAddRemove={true} // if this line is commented, the card will be flipped
        exitButtonSlot={
          <ExitLearnMoreButton
            onClick={(e) => {
              e.preventDefault();
              setLearnMoreActive(false)
            }}
          />
        }
        toolLearnMore={tool.name}
        photoLearnMore={tool.main_image}
        descriptionLearnMore={<span dangerouslySetInnerHTML={{ __html: tool.long_description }} />}
        privacyAgreementLearnMore={<span dangerouslySetInnerHTML={{ __html: tool.privacy_agreement }} />}
        placementsInCanvasLearnMore={tool.canvas_placement_expanded.map(p => p.name).join(', ')}
        supportResourcesLearnMore={<span dangerouslySetInnerHTML={{ __html: tool.support_resources }} />}
      />
    );
  }
}

const ProductCard = React.forwardRef(ProductCard_);

export default ProductCard;
