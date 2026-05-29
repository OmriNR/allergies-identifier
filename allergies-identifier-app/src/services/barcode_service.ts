interface OpenFoodFactsResponse {
    status: number;
    status_verbose: string;
    product?: {
        product_name?: string;
        ingredients_text?: string;
    }
}

interface BarcodeResult {
  found: boolean;
  productName?: string;
  ingredients?: string;
  message?: string;
}

export async function getIngredientsByBarcode(barcode:string): Promise<BarcodeResult> {
    const url = `https://world.openfoodfacts.org/api/v2/product/${barcode}.json`;

    try{

        const response =  await fetch(url,{
            method: 'GET'
        });

        if (!response.ok) {
            return {
                found: false,
                message: `connection failed: ${response.status}`,
            };
        }

        const data : OpenFoodFactsResponse = await response.json();

        if (data.status == 1 && data.product) {
            return {
                found: true,
                productName: data.product.product_name || 'Unknown product',
                ingredients: data.product.ingredients_text || 'No ingredients'
            };
        }
        else {
            return {
                found: false,
                message: 'The product does not exist in the global database'
            }
        }
    }
    catch (error) {
        return {
            found: false,
            message: `Unexpected error: ${error instanceof Error ? error.message : String(error)}`
        }
    }
}