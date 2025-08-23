'use client';

import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { currencies, Currency, getCurrencyByCode } from '@/lib/currencies';

interface CurrencyPickerProps {
  value?: string; // Currency code
  onValueChange: (currency: Currency) => void;
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  className?: string;
}

export function CurrencyPicker({
  value,
  onValueChange,
  disabled = false,
  label,
  placeholder = 'Select currency...',
  className,
}: CurrencyPickerProps) {
  const selectedCurrency = value ? getCurrencyByCode(value) : null;

  const handleValueChange = (currencyCode: string) => {
    const currency = getCurrencyByCode(currencyCode);
    if (currency) {
      onValueChange(currency);
    }
  };

  return (
    <div className={cn('space-y-2', className)}>
      {label && <Label>{label}</Label>}
      <Select value={value} onValueChange={handleValueChange} disabled={disabled}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder}>
            {selectedCurrency && (
              <div className="flex items-center gap-2">
                <span className="font-medium">{selectedCurrency.symbol}</span>
                <span>{selectedCurrency.code}</span>
                <span className="text-muted-foreground">- {selectedCurrency.name}</span>
              </div>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {currencies.map((currency) => (
            <SelectItem key={currency.code} value={currency.code}>
              <div className="flex items-center gap-3">
                <span className="font-medium w-6">{currency.symbol}</span>
                <span className="font-medium w-12">{currency.code}</span>
                <span className="text-muted-foreground">{currency.name}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}